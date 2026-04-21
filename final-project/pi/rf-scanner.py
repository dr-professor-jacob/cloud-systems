#!/usr/bin/env python3
"""RF Survey — rf-scanner.py
Background scanner: runs rtl_433 and readsb on a schedule,
writes results directly to Blob Storage as ism_auto.json / adsb_auto.json.
Coordinates with ingest.py via DEVICE_LOCK.
"""
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SECRETS_FILE  = Path("/run/secrets/rf.env")
DEVICE_LOCK   = Path("/tmp/rtlsdr.lock")
BLOB_RESULTS  = "rfresults"

ISM_INTERVAL  = 3 * 60    # seconds between ISM scans
ADSB_INTERVAL = 3 * 60    # seconds between ADS-B scans
ISM_DURATION  = 25
ADSB_DURATION = 20


def load_env(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def acquire_device(timeout=120) -> bool:
    """Set lock and kill any running SDR processes. Returns True on success."""
    DEVICE_LOCK.touch()
    for proc in (["pkill", "-KILL", "-x", "rtl_power"],
                 ["pkill", "-KILL", "-x", "rtl_fm"],
                 ["pkill", "-KILL", "-x", "rtl_433"],
                 ["pkill", "-KILL", "-f", "readsb"]):
        subprocess.run(proc, capture_output=True)
    time.sleep(8.0)   # USB needs ~5-7s to release after SIGKILL
    return True


def release_device() -> None:
    DEVICE_LOCK.unlink(missing_ok=True)
    log.info("Device lock released")


def scan_ism(duration: int) -> dict:
    """Run rtl_433 and return parsed packets."""
    cmd = ["rtl_433", "-f", "433920000", "-T", str(duration), "-F", "json", "-q"]
    log.info("ISM scan: %s", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 15)
    packets = []
    for line in r.stdout.splitlines():
        try:
            packets.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return {
        "ts":      datetime.now(timezone.utc).isoformat(),
        "count":   len(packets),
        "packets": packets[:20],
        "message": f"{len(packets)} packet(s) decoded" if packets else "No packets — quiet band",
    }


def scan_adsb(duration: int) -> dict:
    """Run readsb and return aircraft list."""
    tmpdir = tempfile.mkdtemp(prefix="adsb_auto_")
    cmd = ["/usr/local/bin/readsb", "--device-type", "rtlsdr", "--gain", "49.6",
           "--quiet", "--write-json", tmpdir, "--write-json-every", "1"]
    log.info("ADS-B scan: %ds → %s", duration, tmpdir)
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=duration)
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        return {"ts": datetime.now(timezone.utc).isoformat(), "aircraft": [], "count": 0,
                "message": "readsb not installed"}

    aircraft_file = Path(tmpdir) / "aircraft.json"
    if not aircraft_file.exists():
        return {"ts": datetime.now(timezone.utc).isoformat(), "aircraft": [], "count": 0,
                "message": "No data — check antenna"}

    try:
        data = json.loads(aircraft_file.read_text())
        aircraft = data.get("aircraft", [])
        clean = []
        for ac in aircraft[:30]:
            entry = {"hex": ac.get("hex", ""), "flight": ac.get("flight", "").strip()}
            if "lat" in ac and "lon" in ac:
                entry["lat"] = round(ac["lat"], 4)
                entry["lon"] = round(ac["lon"], 4)
            for f in ("altitude", "speed", "track"):
                if f in ac:
                    entry[f] = ac[f]
            clean.append(entry)
        return {
            "ts":       datetime.now(timezone.utc).isoformat(),
            "aircraft": clean,
            "count":    len(aircraft),
            "message":  f"{len(aircraft)} aircraft tracked" if aircraft else "No aircraft in range",
        }
    except Exception as e:
        return {"ts": datetime.now(timezone.utc).isoformat(), "aircraft": [], "count": 0,
                "message": f"Parse error: {e}"}


def write_blob(blob_client: BlobServiceClient, name: str, data: dict) -> None:
    b = blob_client.get_blob_client(BLOB_RESULTS, name)
    b.upload_blob(json.dumps(data), overwrite=True)
    log.info("Wrote %s (%d bytes)", name, len(json.dumps(data)))


def main():
    if not SECRETS_FILE.exists():
        log.error("Secrets file not found: %s", SECRETS_FILE)
        sys.exit(1)

    load_env(SECRETS_FILE)
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    if not conn_str:
        log.error("AZURE_STORAGE_CONNECTION_STRING not set")
        sys.exit(1)

    blob_client = BlobServiceClient.from_connection_string(conn_str)
    log.info("Scanner started — ISM every %dm, ADS-B every %dm",
             ISM_INTERVAL // 60, ADSB_INTERVAL // 60)

    last_ism  = time.time()           # don't scan immediately at startup
    last_adsb = time.time() + 90      # stagger ADS-B 90s after ISM

    while True:
        now = time.time()

        if now - last_ism >= ISM_INTERVAL:
            log.info("Starting ISM scan...")
            acquire_device()
            try:
                result = scan_ism(ISM_DURATION)
                write_blob(blob_client, "ism_auto.json", result)
                last_ism = time.time()
            except Exception as e:
                log.error("ISM scan error: %s", e)
            finally:
                release_device()
            time.sleep(5)

        now = time.time()
        if now - last_adsb >= ADSB_INTERVAL:
            log.info("Starting ADS-B scan...")
            acquire_device()
            try:
                result = scan_adsb(ADSB_DURATION)
                write_blob(blob_client, "adsb_auto.json", result)
                last_adsb = time.time()
            except Exception as e:
                log.error("ADS-B scan error: %s", e)
            finally:
                release_device()
            time.sleep(5)

        time.sleep(30)  # check schedule every 30s


if __name__ == "__main__":
    main()
