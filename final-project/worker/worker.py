#!/usr/bin/env python3
"""RF Survey Worker — processes sweep data and demodulation results from Service Bus."""
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import numpy as np
from azure.identity import ManagedIdentityCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
SB_NAMESPACE   = os.environ["SERVICE_BUS_NAMESPACE"]   # e.g. rfsrvy-sb.servicebus.windows.net
STORAGE_URL    = os.environ["STORAGE_ACCOUNT_URL"]      # e.g. https://rfsrvystorage.blob.core.windows.net
CLIENT_ID      = os.environ.get("AZURE_CLIENT_ID")

QUEUE_SWEEPS   = "rf-sweeps"
QUEUE_RESULTS  = "rf-results"
BLOB_SWEEPS    = "rfsweeps"
BLOB_RESULTS   = "rfresults"

EMA_ALPHA           = 0.1    # higher = faster response to changes
BLOB_INTERVAL       = 30     # seconds between Blob writes
ANOMALY_THRESHOLD   = 15.0   # dB above running avg to flag as anomaly
ANOMALY_COOLDOWN    = 300    # seconds before re-flagging same frequency
MIN_SWEEPS_FOR_ANOM = 10     # don't flag until baseline is established

# ---------------------------------------------------------------------------
# Band annotation table — (start_hz, end_hz, label, priority)
# ---------------------------------------------------------------------------
BANDS = [
    (87_500_000,   108_000_000, "FM Broadcast",          "benign"),
    (108_000_000,  137_000_000, "Aviation VHF",          "benign"),
    (137_000_000,  138_000_000, "NOAA Weather Sat",      "benign"),
    (144_000_000,  148_000_000, "Amateur 2m",            "benign"),
    (156_000_000,  174_000_000, "Marine / Land Mobile",  "benign"),
    (162_400_000,  162_550_000, "NOAA Weather Radio",    "benign"),
    (433_050_000,  434_790_000, "ISM 433 MHz",           "interesting"),
    (462_000_000,  467_000_000, "FRS / GMRS",            "benign"),
    (575_000_000,  590_000_000, "LTE Band 7/41",         "benign"),
    (614_000_000,  652_000_000, "LTE Band 71",           "benign"),
    (699_000_000,  716_000_000, "LTE Band 12/17",        "benign"),
    (728_000_000,  768_000_000, "LTE Band 12/13",        "benign"),
    (850_000_000,  900_000_000, "Cellular LTE",          "benign"),
    (902_000_000,  928_000_000, "ISM 915 MHz",           "interesting"),
    (1_090_000_000,1_090_000_000,"ADS-B Aircraft",       "benign"),
    (1_227_600_000,1_227_600_000,"GPS L2",               "benign"),
    (1_575_420_000,1_575_420_000,"GPS L1",               "benign"),
    # Athens, OH ground-truth signals
    (91_300_000,   91_300_000,  "WOUB-FM 91.3",         "benign"),   # Ohio University NPR
    (105_500_000,  105_500_000, "WXTQ 105.5",           "benign"),   # local FM
    (146_625_000,  146_730_000, "W8UKE Repeater",       "benign"),   # OU ARC 2m repeater
    (162_425_000,  162_425_000, "NOAA KZZ46",           "benign"),   # Athens WX radio
]


def annotate_freq(freq_hz: int) -> dict:
    """Return band info for a given frequency, or None."""
    for start, end, label, priority in BANDS:
        if start <= freq_hz <= end:
            return {"label": label, "priority": priority}
    return {"label": None, "priority": "unknown"}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
avg      = None   # numpy array, shape (N,)
peak     = None
min_hold = None
raw      = None   # last single sweep, unaveraged
freq_meta = None  # {freq_start, freq_step, n_bins}
last_blob_write = 0.0
sweep_count      = 0
last_pi_sweep_ts = ""   # set only when a real sweep arrives from Pi
start_time       = time.time()
anomaly_cache    = {}   # freq_mhz_rounded -> last_flagged_timestamp
anomaly_log      = []   # last 20 anomalies [{ts, freq_mhz, power_dbm, excess_db, band}]
last_reset_ts    = ""   # ts of the last reset_requested.json we acted on


RECONNECT_RESET_S = 300   # reset averages if Pi was offline this long


def _reset_state(reason: str) -> None:
    global avg, peak, min_hold, sweep_count, anomaly_cache, anomaly_log
    avg = None; peak = None; min_hold = None
    sweep_count = 0
    anomaly_cache = {}; anomaly_log = []
    log.info("Averages reset: %s", reason)


def _check_reset_request() -> None:
    """Check for a dashboard-triggered reset (new location button)."""
    global last_reset_ts
    try:
        blob = blob_client.get_blob_client(BLOB_SWEEPS, "reset_requested.json")
        data = json.loads(blob.download_blob().readall())
        ts = data.get("ts", "")
        if ts and ts != last_reset_ts:
            last_reset_ts = ts
            _reset_state(f"dashboard reset requested at {ts}")
    except Exception:
        pass  # blob doesn't exist = no reset pending


def process_sweep(data: dict) -> None:
    """Update running avg, peak, min_hold, and raw from a new sweep."""
    global avg, peak, min_hold, raw, freq_meta, last_blob_write, sweep_count, last_pi_sweep_ts

    # Check for dashboard-triggered location reset
    _check_reset_request()

    # If Pi reconnects after a long gap, stale averages from the old location
    # would contaminate the new readings — reset and start fresh.
    if last_pi_sweep_ts and avg is not None:
        gap_s = (datetime.now(timezone.utc)
                 - datetime.fromisoformat(last_pi_sweep_ts)).total_seconds()
        if gap_s > RECONNECT_RESET_S:
            _reset_state(f"Pi reconnected after {gap_s:.0f}s offline")

    bins = np.array(data["bins"], dtype=np.float32)
    n = len(bins)
    raw = bins.copy()

    if avg is None:
        avg      = bins.copy()
        peak     = bins.copy()
        min_hold = bins.copy()
        freq_meta = {
            "freq_start": data["freq_start"],
            "freq_step":  data["freq_step"],
            "n_bins":     n,
        }
        log.info("Baseline initialized with %d bins", n)
    else:
        avg      = EMA_ALPHA * bins + (1 - EMA_ALPHA) * avg
        peak     = np.maximum(peak, bins)
        min_hold = np.minimum(min_hold, bins)

    sweep_count += 1
    last_pi_sweep_ts = datetime.now(timezone.utc).isoformat()

    # Anomaly detection — only after baseline is established
    if sweep_count >= MIN_SWEEPS_FOR_ANOM and raw is not None:
        _detect_anomalies(raw, avg, freq_meta)


def _detect_anomalies(raw_bins, avg_bins, meta) -> None:
    global anomaly_cache, anomaly_log
    now     = time.time()
    n       = len(raw_bins)
    fstart  = meta["freq_start"]
    fstep   = meta["freq_step"]

    for i in range(1, n - 1):
        excess = float(raw_bins[i]) - float(avg_bins[i])
        if (excess >= ANOMALY_THRESHOLD
                and raw_bins[i] > raw_bins[i - 1]
                and raw_bins[i] > raw_bins[i + 1]):
            freq_hz  = fstart + i * fstep
            freq_mhz = round(freq_hz / 1e6, 2)
            key      = round(freq_mhz)
            if key in anomaly_cache and now - anomaly_cache[key] < ANOMALY_COOLDOWN:
                continue
            anomaly_cache[key] = now
            band = annotate_freq(int(freq_hz))
            entry = {
                "ts":        datetime.now(timezone.utc).isoformat(),
                "freq_mhz":  freq_mhz,
                "power_dbm": round(float(raw_bins[i]), 1),
                "excess_db": round(excess, 1),
                "band":      band["label"] or "Unknown",
            }
            anomaly_log.insert(0, entry)
            anomaly_log[:] = anomaly_log[:20]   # keep last 20
            log.info("Anomaly: %.2f MHz  +%.1f dB above avg  (%s)",
                     freq_mhz, excess, entry["band"])


def _write_sweep_blob() -> None:
    """Write current averaged spectrum + peak/min/raw to Blob Storage."""
    if avg is None:
        return
    ts = datetime.now(timezone.utc).isoformat()
    def clean(arr):
        return [0.0 if (v != v or v == float('inf') or v == float('-inf')) else round(float(v), 2) for v in arr]

    payload = {
        "ts":         ts,
        "freq_start": freq_meta["freq_start"],
        "freq_step":  freq_meta["freq_step"],
        "n_bins":     freq_meta["n_bins"],
        "avg":        clean(avg),
        "peak":       clean(peak),
        "min_hold":   clean(min_hold),
        "raw":        clean(raw) if raw is not None else [],
    }
    blob = blob_client.get_blob_client(BLOB_SWEEPS, "latest.json")
    blob.upload_blob(json.dumps(payload), overwrite=True)

    # Write stats.json — worker health visible to dashboard
    peak_idx  = int(np.argmax(peak))
    peak_freq = (freq_meta["freq_start"] + peak_idx * freq_meta["freq_step"]) / 1e6
    noise_reduction_db = round(5 * np.log10(max(sweep_count, 1)), 1)
    stats = {
        "sweep_count":        sweep_count,
        "uptime_s":           int(time.time() - start_time),
        "last_sweep_ts":      ts,
        "last_pi_sweep_ts":   last_pi_sweep_ts,   # only updated when Pi sends data
        "n_bins":             freq_meta["n_bins"],
        "peak_max_dbm":       round(float(np.max(peak)), 1),
        "peak_freq_mhz":      round(peak_freq, 2),
        "noise_reduction_db": noise_reduction_db,
        "ema_alpha":          EMA_ALPHA,
    }
    stats_blob = blob_client.get_blob_client(BLOB_SWEEPS, "stats.json")
    stats_blob.upload_blob(json.dumps(stats), overwrite=True)

    # Write anomaly log
    if anomaly_log:
        anom_blob = blob_client.get_blob_client(BLOB_RESULTS, "anomalies.json")
        anom_blob.upload_blob(json.dumps(anomaly_log), overwrite=True)

    # Also archive timestamped snapshot
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_blob = blob_client.get_blob_client(BLOB_SWEEPS, f"{date_str}/{ts}.json")
    archive_blob.upload_blob(json.dumps(payload), overwrite=True)
    log.info("Blob updated — sweep #%d, peak %.1f dBm @ %.2f MHz, noise reduction %.1f dB",
             sweep_count, float(np.max(peak)), peak_freq, noise_reduction_db)


def process_result(data: dict) -> None:
    """Store a demodulation result from the Pi dispatcher to Blob."""
    job_id = data.get("job_id")
    if not job_id:
        log.warning("Received rf-result with no job_id")
        return
    blob = blob_client.get_blob_client(BLOB_RESULTS, f"{job_id}.json")
    blob.upload_blob(json.dumps(data), overwrite=True)
    log.info("Stored result for job %s", job_id)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def blob_writer_thread():
    """Write blob every BLOB_INTERVAL seconds regardless of sweep arrival."""
    while True:
        time.sleep(BLOB_INTERVAL)
        if avg is not None:
            try:
                _write_sweep_blob()
            except Exception as e:
                log.error("Background blob write error: %s", e)


def main():
    global blob_client

    cred = ManagedIdentityCredential(client_id=CLIENT_ID)
    sb   = ServiceBusClient(SB_NAMESPACE, cred)
    blob_client = BlobServiceClient(STORAGE_URL, credential=cred)

    # Start background blob writer thread
    t = threading.Thread(target=blob_writer_thread, daemon=True)
    t.start()

    log.info("Worker started — listening on %s and %s", QUEUE_SWEEPS, QUEUE_RESULTS)

    sweep_receiver  = sb.get_queue_receiver(QUEUE_SWEEPS,  max_wait_time=2)
    result_receiver = sb.get_queue_receiver(QUEUE_RESULTS, max_wait_time=1)

    with sweep_receiver, result_receiver:
        while True:
            # Process up to 5 sweep messages per iteration
            for msg in sweep_receiver.receive_messages(max_message_count=5, max_wait_time=2):
                try:
                    data = json.loads(str(msg))
                    process_sweep(data)
                    sweep_receiver.complete_message(msg)
                except Exception as e:
                    log.error("Sweep processing error: %s", e)
                    sweep_receiver.abandon_message(msg)

            # Drain rf-results queue
            for msg in result_receiver.receive_messages(max_message_count=5, max_wait_time=1):
                try:
                    data = json.loads(str(msg))
                    process_result(data)
                    result_receiver.complete_message(msg)
                except Exception as e:
                    log.error("Result processing error: %s", e)
                    result_receiver.abandon_message(msg)


if __name__ == "__main__":
    main()
