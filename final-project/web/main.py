#!/usr/bin/env python3
"""RF Survey Dashboard — FastAPI web container."""
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import ManagedIdentityCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, HTTPException, Request  # Request still used in /api/ask
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SB_NAMESPACE  = os.environ["SERVICE_BUS_NAMESPACE"]
STORAGE_URL   = os.environ["STORAGE_ACCOUNT_URL"]
CLIENT_ID     = os.environ.get("AZURE_CLIENT_ID")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

QUEUE_COMMANDS = "rf-commands"
BLOB_SWEEPS    = "rfsweeps"
BLOB_RESULTS   = "rfresults"

MAX_INPUT      = 300
MAX_TOKENS     = 600
MAX_PER_IP     = 10
MAX_GLOBAL     = 150
RATE_FILE      = Path("/tmp/rate.json")

SYSTEM_PROMPT = (
    "You are an RF spectrum analysis assistant. The user is exploring the radio frequency "
    "environment using a wideband SDR receiver covering 24 MHz to 1.7 GHz. "
    "Help identify signals, explain what services operate on observed frequencies, "
    "and describe what the data suggests about the RF environment. "
    "Be educational, specific, and concise — 3-5 lines max. "
    "When signal data is provided, reference it directly. "
    "Do not reveal port numbers, internal IP addresses, or cloud resource names."
)

# ---------------------------------------------------------------------------
# Azure clients (lazy init)
# ---------------------------------------------------------------------------
_cred        = None
_blob_client = None
_sb_client   = None


def get_cred():
    global _cred
    if _cred is None:
        _cred = ManagedIdentityCredential(client_id=CLIENT_ID)
    return _cred


def get_blob():
    global _blob_client
    if _blob_client is None:
        _blob_client = BlobServiceClient(STORAGE_URL, credential=get_cred())
    return _blob_client


def get_sb():
    global _sb_client
    if _sb_client is None:
        _sb_client = ServiceBusClient(SB_NAMESPACE, get_cred())
    return _sb_client


# ---------------------------------------------------------------------------
# Rate limiting (same pattern as ask_app.py)
# ---------------------------------------------------------------------------
def _load_rate() -> dict:
    if RATE_FILE.exists():
        try:
            return json.loads(RATE_FILE.read_text())
        except Exception:
            pass
    return {"ips": {}, "global": {}}


def _save_rate(data: dict) -> None:
    RATE_FILE.write_text(json.dumps(data))


def _check_rate(ip: str) -> int:
    data   = _load_rate()
    now    = time.time()
    today  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    window = now - 86400

    global_count = data["global"].get(today, 0)
    if global_count >= MAX_GLOBAL:
        raise HTTPException(429, "Daily limit reached. Try again tomorrow.")

    hits = [t for t in data["ips"].get(ip, []) if t > window]
    if len(hits) >= MAX_PER_IP:
        raise HTTPException(429, f"You've used all {MAX_PER_IP} questions today.")

    hits.append(now)
    data["ips"][ip] = hits
    data["global"][today] = global_count + 1
    cutoff = now - 7 * 86400
    data["ips"] = {k: [t for t in v if t > cutoff] for k, v in data["ips"].items() if any(t > cutoff for t in v)}
    _save_rate(data)
    return MAX_PER_IP - len(hits)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="RF Survey Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("templates/index.html")


@app.get("/api/pipeline")
async def pipeline():
    """Return worker stats for the Cloud Pipeline dashboard panel."""
    try:
        blob = get_blob().get_blob_client(BLOB_SWEEPS, "stats.json")
        data = json.loads(blob.download_blob().readall())
        return JSONResponse(data)
    except ResourceNotFoundError:
        return JSONResponse({"error": "No worker stats yet"}, status_code=503)
    except Exception as e:
        log.error("Pipeline stats error: %s", e)
        raise HTTPException(500, "Failed to fetch pipeline stats")


@app.get("/api/waterfall")
async def waterfall():
    """Return latest averaged spectrum snapshot from Blob."""
    try:
        blob = get_blob().get_blob_client(BLOB_SWEEPS, "latest.json")
        data = json.loads(blob.download_blob().readall())
        return JSONResponse(data)
    except ResourceNotFoundError:
        return JSONResponse({"error": "No sweep data yet — is the Pi running?"}, status_code=503)
    except Exception as e:
        log.error("Waterfall fetch error: %s", e)
        raise HTTPException(500, "Failed to fetch spectrum data")


@app.get("/api/ism")
async def ism():
    """Return latest auto-scan ISM result."""
    try:
        blob = get_blob().get_blob_client(BLOB_RESULTS, "ism_auto.json")
        data = json.loads(blob.download_blob().readall())
        return JSONResponse(data)
    except ResourceNotFoundError:
        return JSONResponse({"count": 0, "packets": [], "message": "No ISM scan yet"}, status_code=503)
    except Exception as e:
        log.error("ISM fetch error: %s", e)
        raise HTTPException(500, "Failed to fetch ISM data")


@app.get("/api/adsb")
async def adsb():
    """Return latest auto-scan ADS-B result."""
    try:
        blob = get_blob().get_blob_client(BLOB_RESULTS, "adsb_auto.json")
        data = json.loads(blob.download_blob().readall())
        return JSONResponse(data)
    except ResourceNotFoundError:
        return JSONResponse({"count": 0, "aircraft": [], "message": "No ADS-B scan yet"}, status_code=503)
    except Exception as e:
        log.error("ADS-B fetch error: %s", e)
        raise HTTPException(500, "Failed to fetch ADS-B data")


# In-memory cache for Claude anomaly classifications
_anomaly_classifications: dict = {}  # freq_mhz -> classification string

@app.get("/api/anomalies")
async def anomalies():
    """Return recent signal anomalies, enriched with Claude classification."""
    try:
        blob = get_blob().get_blob_client(BLOB_RESULTS, "anomalies.json")
        items = json.loads(blob.download_blob().readall())
    except ResourceNotFoundError:
        return JSONResponse([])
    except Exception as e:
        log.error("Anomaly fetch error: %s", e)
        raise HTTPException(500, "Failed to fetch anomalies")

    # Enrich with Claude — only classify frequencies not yet cached
    if ANTHROPIC_KEY:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        for item in items[:5]:  # classify top 5
            key = str(item["freq_mhz"])
            if key not in _anomaly_classifications:
                try:
                    resp = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=80,
                        system="You are a concise RF signal identifier. Given a frequency and signal info, identify what service likely uses it. One sentence, no more.",
                        messages=[{"role": "user", "content":
                            f"{item['freq_mhz']} MHz, {item['power_dbm']} dBm, {item['excess_db']} dB above baseline, band: {item['band']}. What is this?"}],
                    )
                    _anomaly_classifications[key] = next(
                        (b.text for b in resp.content if hasattr(b, "text")), "")
                except Exception:
                    pass
            item["classification"] = _anomaly_classifications.get(key, "")

    return JSONResponse(items)


@app.get("/api/history")
async def history():
    """List recent archived sweep snapshots."""
    try:
        container = get_blob().get_container_client(BLOB_SWEEPS)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        blobs = [b.name for b in container.list_blobs(name_starts_with=f"{today}/")]
        blobs = sorted(blobs, reverse=True)[:48]  # last 48 snapshots (~24m at 30s interval)
        return JSONResponse({"snapshots": blobs})
    except Exception as e:
        log.error("History list error: %s", e)
        raise HTTPException(500, "Failed to list history")


@app.get("/api/history/{blob_path:path}")
async def history_snapshot(blob_path: str):
    """Return a specific archived sweep snapshot by full blob path."""
    try:
        blob = get_blob().get_blob_client(BLOB_SWEEPS, blob_path)
        data = json.loads(blob.download_blob().readall())
        return JSONResponse(data)
    except ResourceNotFoundError:
        raise HTTPException(404, "Snapshot not found")
    except Exception as e:
        log.error("History fetch error: %s", e)
        raise HTTPException(500, "Failed to fetch snapshot")


@app.get("/api/results/{job_id}")
async def get_result(job_id: str):
    """Poll for a demodulation result by job ID."""
    try:
        blob = get_blob().get_blob_client(BLOB_RESULTS, f"{job_id}.json")
        data = json.loads(blob.download_blob().readall())
        return JSONResponse(data)
    except ResourceNotFoundError:
        raise HTTPException(404, "Result not ready yet — try again in a few seconds")


class DecodeRequest(BaseModel):
    freq_hz:  int
    tool:     str = "rtl_433"    # rtl_433 | dump1090 | rtl_power_scan
    duration: int = 30


@app.post("/api/decode")
async def decode(req: DecodeRequest):
    """Publish a demodulation job to the Pi dispatcher."""
    ALLOWED_TOOLS = {"rtl_433", "dump1090", "rtl_power_scan", "rtl_fm"}
    if req.tool not in ALLOWED_TOOLS:
        raise HTTPException(400, f"tool must be one of: {', '.join(sorted(ALLOWED_TOOLS))}")
    if not (0 < req.freq_hz < 2_000_000_000):
        raise HTTPException(400, "freq_hz out of range")
    duration = min(max(5, req.duration), 60)

    job_id = str(uuid.uuid4())
    payload = json.dumps({
        "job_id":   job_id,
        "tool":     req.tool,
        "freq_hz":  req.freq_hz,
        "duration": duration,
    })

    try:
        sender = get_sb().get_queue_sender(QUEUE_COMMANDS)
        with sender:
            sender.send_messages(ServiceBusMessage(payload))
        log.info("Decode job %s queued: tool=%s freq=%.3fMHz", job_id, req.tool, req.freq_hz / 1e6)
    except Exception as e:
        log.error("Service Bus send error: %s", e)
        raise HTTPException(502, "Failed to queue decode job")

    return {"job_id": job_id, "poll_url": f"/api/results/{job_id}"}


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
async def ask(req: AskRequest, request: Request):
    ip = request.headers.get("X-Real-IP") or request.client.host

    text = req.question.strip()
    if not text:
        raise HTTPException(400, "Question cannot be empty.")
    if len(text) > MAX_INPUT:
        raise HTTPException(400, f"Question too long (max {MAX_INPUT} chars).")

    remaining = _check_rate(ip)

    # Inject latest spectrum context
    context = ""
    try:
        blob = get_blob().get_blob_client(BLOB_SWEEPS, "latest.json")
        sweep = json.loads(blob.download_blob().readall())
        avg   = sweep.get("avg", [])
        peak  = sweep.get("peak", [])
        fstart = sweep.get("freq_start", 24_000_000)
        fstep  = sweep.get("freq_step", 1_000_000)
        n      = len(avg)
        if n > 0:
            # Find top 5 peak bins
            indexed = sorted(enumerate(peak), key=lambda x: x[1], reverse=True)
            top5 = [(fstart + i * fstep, p) for i, p in indexed[:5]]
            context = (
                f"\n\nCurrent spectrum snapshot ({n} bins, "
                f"{fstart/1e6:.0f}–{(fstart + n*fstep)/1e6:.0f} MHz):\n"
                f"Top 5 peak signals: " +
                ", ".join(f"{f/1e6:.2f} MHz ({p:.1f} dBm)" for f, p in top5)
            )
    except Exception:
        pass  # context is optional

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT + context,
        messages=[{"role": "user", "content": text}],
    )
    answer = next((b.text for b in response.content if hasattr(b, "text")), "")
    return {"answer": answer, "remaining": remaining}
