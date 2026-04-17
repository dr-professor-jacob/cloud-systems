#!/usr/bin/env python3
"""RF Survey — Pi dispatcher.py
Polls rf-commands queue, runs demodulation tools, publishes results to rf-results.
Supported tools: rtl_433, dump1090 (via rtl_adsb), rtl_power (sub-scan)
"""
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

SECRETS_FILE   = Path("/run/secrets/rf.env")
QUEUE_COMMANDS = "rf-commands"
QUEUE_RESULTS  = "rf-results"
MAX_DURATION   = 60   # cap any job at 60 seconds

TOOL_ALLOWLIST = {"rtl_433", "dump1090", "rtl_power_scan", "rtl_fm"}
DEVICE_LOCK    = Path("/tmp/rtlsdr.lock")   # held while dongle is in use


def load_env(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


# ---------------------------------------------------------------------------
# Tool runners
# ---------------------------------------------------------------------------
def run_rtl433(freq_hz: int, duration: int) -> str:
    """Decode ISM 433/915 MHz sensor packets."""
    cmd = [
        "rtl_433",
        "-f", str(freq_hz),
        "-T", str(duration),
        "-F", "json",
        "-q",           # quiet mode
    ]
    log.info("Running: %s", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 15)
    output = r.stdout.strip()
    if not output:
        return f"No decodable packets found on {freq_hz/1e6:.3f} MHz in {duration}s."
    # rtl_433 -F json emits one JSON object per line
    packets = []
    for line in output.splitlines():
        try:
            packets.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if not packets:
        return f"rtl_433 output ({len(output)} bytes) but no valid JSON packets."
    summary = f"{len(packets)} packet(s) decoded on {freq_hz/1e6:.3f} MHz:\n"
    for p in packets[:10]:   # cap at 10 to keep message small
        summary += json.dumps(p) + "\n"
    return summary.strip()


def run_dump1090(duration: int) -> str:
    """Capture ADS-B aircraft transponder messages (1090 MHz) using dump1090 --write-json."""
    import tempfile, json as _json, os
    tmpdir = tempfile.mkdtemp(prefix="dump1090_")
    cmd = [
        "dump1090",
        "--quiet",
        "--write-json", tmpdir,
        "--write-json-every", "1",
        "--net",          # enable network output (needed for --write-json)
    ]
    log.info("Running dump1090 for %ds → %s", duration, tmpdir)
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=duration)
    except subprocess.TimeoutExpired:
        pass  # expected — we kill it after duration
    except FileNotFoundError:
        return "dump1090 not installed. Install with: sudo apt install dump1090-mutability"

    aircraft_file = os.path.join(tmpdir, "aircraft.json")
    if not os.path.exists(aircraft_file):
        return "No ADS-B data captured — aircraft may be out of range or dump1090 failed to start."

    try:
        data = _json.loads(open(aircraft_file).read())
        aircraft = data.get("aircraft", [])
        if not aircraft:
            return "No aircraft tracked during capture window."
        lines = []
        for ac in aircraft[:20]:
            parts = [ac.get("flight", "???").strip()]
            if "lat" in ac and "lon" in ac:
                parts.append(f"pos={ac['lat']:.3f},{ac['lon']:.3f}")
            if "altitude" in ac:
                parts.append(f"alt={ac['altitude']}ft")
            lines.append("  " + "  ".join(parts))
        return f"{len(aircraft)} aircraft tracked:\n" + "\n".join(lines)
    except Exception as e:
        return f"Parse error: {e}"


def run_rtl_fm(freq_hz: int, duration: int) -> str:
    """Capture FM audio, transcode to MP3 via ffmpeg, upload to Blob, return URL.
    Requires: ffmpeg installed (sudo apt install ffmpeg)
    Requires: AZURE_STORAGE_* env vars set (same rf.env secrets file).
    """
    import tempfile, os
    out_mp3 = f"/tmp/rf_audio_{freq_hz}.mp3"

    # Determine mode: wideband FM for broadcast band, narrowband for others
    freq_mhz = freq_hz / 1e6
    if 87.5 <= freq_mhz <= 108:
        mode, sample_rate = "wbfm", "170k"
    else:
        mode, sample_rate = "fm", "24k"

    # rtl_fm | ffmpeg → mp3  (timeout kills rtl_fm after duration seconds)
    cmd = (
        f"timeout {duration} rtl_fm -M {mode} -f {freq_hz} -s {sample_rate} - "
        f"| ffmpeg -y -f s16le -ac 1 -ar {sample_rate} -i pipe:0 "
        f"-codec:a libmp3lame -b:a 64k {out_mp3}"
    )
    log.info("Running rtl_fm | ffmpeg for %ds @ %.3f MHz", duration, freq_mhz)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=duration + 30)

    if not os.path.exists(out_mp3) or os.path.getsize(out_mp3) < 1024:
        return f"rtl_fm capture failed or produced empty output. stderr: {r.stderr[:200]}"

    # Upload to Blob Storage using connection string
    storage_conn = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    storage_url  = os.environ.get("STORAGE_ACCOUNT_URL", "")
    if storage_conn:
        try:
            from azure.storage.blob import BlobServiceClient
            import time as _time
            blob_name = f"audio/{freq_hz}_{int(_time.time())}.mp3"
            client = BlobServiceClient.from_connection_string(storage_conn)
            with open(out_mp3, "rb") as f:
                client.get_blob_client("rfresults", blob_name).upload_blob(f, overwrite=True)
            os.unlink(out_mp3)
            return f"audio_url:{storage_url}/rfresults/{blob_name}"
        except Exception as e:
            log.error("Blob upload failed: %s", e)

    size_kb = os.path.getsize(out_mp3) // 1024
    return f"Audio captured ({size_kb} KB) but storage not configured."


def run_rtlpower_scan(freq_hz: int, duration: int) -> str:
    """High-resolution sub-scan of ±2 MHz around the clicked frequency."""
    start = max(0, freq_hz - 2_000_000)
    end   = freq_hz + 2_000_000
    outfile = f"/tmp/subscan_{freq_hz}.csv"
    cmd = [
        "rtl_power",
        "-f", f"{start}:{end}:25k",   # 25 kHz resolution
        "-i", str(duration),
        "-1",
        outfile,
    ]
    log.info("Running sub-scan: %s", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 20)
    if r.returncode != 0:
        return f"Sub-scan failed: {r.stderr[:100]}"

    # Parse and summarize: find peak bin
    peak_freq, peak_dbm = None, -999.0
    try:
        import csv as csv_mod
        with open(outfile) as f:
            for row in csv_mod.reader(f):
                if len(row) < 7:
                    continue
                hz_low  = float(row[2])
                hz_step = float(row[4])
                for i, v in enumerate(row[6:]):
                    dbm = float(v.strip())
                    if dbm > peak_dbm:
                        peak_dbm  = dbm
                        peak_freq = hz_low + i * hz_step
    except Exception as e:
        return f"Sub-scan CSV parse error: {e}"

    if peak_freq is None:
        return "Sub-scan produced no data."
    return (f"Sub-scan {start/1e6:.2f}–{end/1e6:.2f} MHz @ 25 kHz resolution:\n"
            f"Peak signal: {peak_freq/1e6:.4f} MHz at {peak_dbm:.1f} dBm")


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
def dispatch(job: dict) -> str:
    tool     = job.get("tool", "")
    freq_hz  = int(job.get("freq_hz", 0))
    duration = min(int(job.get("duration", 30)), MAX_DURATION)

    if tool not in TOOL_ALLOWLIST:
        return f"Unknown tool: {tool!r}. Allowed: {', '.join(sorted(TOOL_ALLOWLIST))}"

    # Stop any in-flight rtl_power sweep, then claim the dongle
    subprocess.run(["pkill", "-TERM", "rtl_power"], capture_output=True)
    time.sleep(1.5)   # give USB stack time to release the device
    DEVICE_LOCK.touch()
    log.info("Device lock acquired for tool=%s", tool)
    try:
        if tool == "rtl_433":
            return run_rtl433(freq_hz, duration)
        elif tool == "dump1090":
            return run_dump1090(duration)
        elif tool == "rtl_fm":
            return run_rtl_fm(freq_hz, duration)
        elif tool == "rtl_power_scan":
            return run_rtlpower_scan(freq_hz, duration)
        return "Unhandled tool"
    finally:
        DEVICE_LOCK.unlink(missing_ok=True)
        log.info("Device lock released")


def main():
    if not SECRETS_FILE.exists():
        log.error("Secrets file not found: %s — run fetch_secrets.sh first", SECRETS_FILE)
        sys.exit(1)

    load_env(SECRETS_FILE)
    conn_str = os.environ.get("SERVICE_BUS_CONNECTION_STRING")
    if not conn_str:
        log.error("SERVICE_BUS_CONNECTION_STRING not set in %s", SECRETS_FILE)
        sys.exit(1)

    sb       = ServiceBusClient.from_connection_string(conn_str)
    receiver = sb.get_queue_receiver(QUEUE_COMMANDS, max_wait_time=30)
    sender   = sb.get_queue_sender(QUEUE_RESULTS)

    log.info("Dispatcher started — listening on '%s'", QUEUE_COMMANDS)

    with receiver, sender:
        while True:
            for msg in receiver.receive_messages(max_message_count=1, max_wait_time=30):
                try:
                    job = json.loads(str(msg))
                    log.info("Job received: tool=%s freq=%.3f MHz duration=%ss",
                             job.get("tool"), job.get("freq_hz", 0) / 1e6, job.get("duration"))

                    output = dispatch(job)
                    result = {
                        "job_id":  job.get("job_id"),
                        "tool":    job.get("tool"),
                        "freq_hz": job.get("freq_hz"),
                        "ts":      datetime.now(timezone.utc).isoformat(),
                        "output":  output,
                    }
                    sender.send_messages(ServiceBusMessage(json.dumps(result)))
                    receiver.complete_message(msg)
                    log.info("Job %s complete", job.get("job_id"))
                except Exception as e:
                    log.error("Dispatch error: %s", e)
                    receiver.abandon_message(msg)


if __name__ == "__main__":
    main()
