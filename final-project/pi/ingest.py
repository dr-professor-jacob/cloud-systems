#!/usr/bin/env python3
"""RF Survey — Pi ingest.py
Runs rtl_power sweep, parses output, and publishes to Azure Service Bus.
Reads SERVICE_BUS_CONNECTION_STRING from /run/secrets/rf.env at startup.
"""
import csv
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from azure.servicebus import ServiceBusClient, ServiceBusMessage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SECRETS_FILE  = Path("/run/secrets/rf.env")
SWEEP_CSV     = Path("/tmp/rf_sweep.csv")
QUEUE_SWEEPS  = "rf-sweeps"
DEVICE_LOCK   = Path("/tmp/rtlsdr.lock")   # dispatcher sets this while using the dongle

# Sweep parameters — adjust to taste
FREQ_START    = "24M"
FREQ_END      = "1700M"
FREQ_STEP     = "1M"        # 1 MHz bins → 1676 bins total
INTEGRATION   = "10"        # seconds per sweep
CROP_PCT      = "30%"       # crop edges of each RTL-SDR tuning window
NODE_ID       = "pi-node"


def load_env(path: Path) -> None:
    """Load KEY=VALUE pairs from file into os.environ."""
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def parse_rtlpower_csv(path: Path) -> tuple[list[float], int, int]:
    """Parse rtl_power CSV into a flat list of power values.

    Returns:
        bins      — list of dBm floats (indexed by 1 MHz bin from freq_start)
        freq_start — Hz
        freq_step  — Hz
    """
    freq_start = None
    freq_step  = None
    bin_map: dict[int, float] = {}

    with open(path, newline="") as f:
        for row in csv.reader(f):
            if len(row) < 7:
                continue
            # date, time, hz_low, hz_high, hz_step, n_samples, *values
            hz_low   = int(float(row[2]))
            hz_step  = int(float(row[4]))
            values   = [float(v) for v in row[6:] if v.strip()]

            if freq_start is None:
                freq_start = hz_low
                freq_step  = hz_step

            for i, dbm in enumerate(values):
                freq_bin = hz_low + i * hz_step
                bin_map[freq_bin] = dbm

    if not bin_map:
        return [], 0, 0

    sorted_freqs = sorted(bin_map.keys())
    bins = [bin_map[f] for f in sorted_freqs]
    return bins, sorted_freqs[0], freq_step


def sweep_once() -> dict | None:
    """Run rtl_power once and return parsed sweep dict, or None on error."""
    # Wait if dispatcher is actively using the dongle
    waited = 0
    while DEVICE_LOCK.exists():
        if waited == 0:
            log.info("Dongle in use by dispatcher — waiting...")
        time.sleep(1)
        waited += 1
        if waited > 120:
            log.warning("Lock held >120s — ignoring and attempting sweep")
            break

    SWEEP_CSV.unlink(missing_ok=True)

    cmd = [
        "rtl_power",
        "-f", f"{FREQ_START}:{FREQ_END}:{FREQ_STEP}",
        "-i", INTEGRATION,
        "-1",           # one sweep then exit
        "-c", CROP_PCT,
        str(SWEEP_CSV),
    ]
    log.info("Starting sweep: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        log.error("rtl_power error: %s", result.stderr[:200])
        return None

    bins, freq_start, freq_step = parse_rtlpower_csv(SWEEP_CSV)
    if not bins:
        log.warning("Empty sweep output")
        return None

    log.info("Sweep complete: %d bins, %.1f–%.1f MHz",
             len(bins), freq_start / 1e6, (freq_start + len(bins) * freq_step) / 1e6)

    return {
        "ts":         datetime.now(timezone.utc).isoformat(),
        "node_id":    NODE_ID,
        "freq_start": freq_start,
        "freq_step":  freq_step,
        "bins":       bins,          # compact: list of dBm floats
    }


def main():
    if not SECRETS_FILE.exists():
        log.error("Secrets file not found: %s — run fetch_secrets.sh first", SECRETS_FILE)
        sys.exit(1)

    load_env(SECRETS_FILE)
    conn_str = os.environ.get("SERVICE_BUS_CONNECTION_STRING")
    if not conn_str:
        log.error("SERVICE_BUS_CONNECTION_STRING not set in %s", SECRETS_FILE)
        sys.exit(1)

    sb = ServiceBusClient.from_connection_string(conn_str)
    sender = sb.get_queue_sender(QUEUE_SWEEPS)

    log.info("Ingest started — publishing to queue '%s'", QUEUE_SWEEPS)

    with sender:
        while True:
            sweep = sweep_once()
            if sweep:
                payload = json.dumps(sweep)
                sender.send_messages(ServiceBusMessage(payload))
                log.info("Published sweep (%d bytes)", len(payload))
            else:
                log.warning("Skipping failed sweep, retrying in 10s")
                time.sleep(10)


if __name__ == "__main__":
    main()
