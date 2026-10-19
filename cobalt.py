"""Cobalt API fallback for YouTube.

When yt-dlp is bot-checked (Vercel datacenter IP), a public cobalt
instance can fetch the video from ITS IP and tunnel the finished file
back to us. The bot then uploads that file to the user.

Cobalt is open-source (MIT) and its public instances expose this exact
POST API. Instances are tried in order; the first one that returns a
usable tunnel/redirect URL wins. An env override (COBALT_INSTANCES,
comma-separated) replaces the built-in list.

API (cobalt 7+/10): POST {instance}/ with JSON
  {"url", "vQuality", "filenameStyle", "downloadMode", ...}
→ {"status": "tunnel"|"redirect"|"picker"|"error", "url", "filename", ...}
"tunnel" = the instance streams the file itself (works from Vercel).
"redirect" = a direct googlevideo URL (blocked from Vercel — we only
use it as a last resort and hand it to the user, whose phone IP works).
"""

import json
import logging
import os
import urllib.error
import urllib.request

log = logging.getLogger("zyrox.cobalt")

DEFAULT_INSTANCES = [
    "https://cobalt-api.kwiatekmiki.com",  # no API key required
    "https://cobalt.meowing.de",           # recommended for YouTube
    "https://co.wuk.sh",
]

TIMEOUT = 60


def _instances() -> list[str]:
    raw = os.getenv("COBALT_INSTANCES", "").strip()
    if raw:
        return [u.strip().rstrip("/") for u in raw.split(",") if u.strip()]
    return list(DEFAULT_INSTANCES)


def _post(instance: str, payload: dict) -> dict:
    req = urllib.request.Request(
        instance + "/",
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ZYROX-Video-Downloader/1.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def fetch(url: str, mode: str = "video", quality: str = "720") -> dict:
    """Ask cobalt instances for a downloadable file.

    mode: "video" (mp4) or "audio" (mp3).
    Returns {"kind": "tunnel"|"redirect", "url", "filename", "instance"}.
    Raises RuntimeError when every instance fails.
    """
    payload: dict = {
        "url": url,
        "filenameStyle": "basic",
    }
    if mode == "audio":
        payload.update({"downloadMode": "audio", "audioFormat": "mp3",
                        "audioBitrate": "128"})
    else:
        payload.update({"downloadMode": "auto", "vQuality": quality})

    errors: list[str] = []
    for inst in _instances():
        try:
            res = _post(inst, payload)
        except urllib.error.HTTPError as e:
            errors.append(f"{inst}: HTTP {e.code}")
            continue
        except Exception as e:
            errors.append(f"{inst}: {type(e).__name__}: {e}")
            continue
        status = res.get("status")
        if status in ("tunnel", "redirect") and res.get("url"):
            return {
                "kind": status,
                "url": res["url"],
                "filename": res.get("filename") or "video.mp4",
                "instance": inst,
            }
        if status == "picker" and res.get("picker"):
            # Multiple items (e.g. a gallery) — take the first usable one.
            for item in res["picker"]:
                if item.get("url"):
                    return {"kind": "tunnel", "url": item["url"],
                            "filename": "video.mp4", "instance": inst}
        errors.append(f"{inst}: status={status} "
                      f"{(res.get('error') or {}).get('code', '')}")
    raise RuntimeError("Cobalt failed: " + "; ".join(errors))


def download_file(file_url: str, dest: str, max_bytes: int,
                  timeout: int = 120) -> int:
    """Stream a cobalt tunnel URL to disk. Returns bytes written.
    Raises ValueError when the file exceeds max_bytes."""
    req = urllib.request.Request(file_url, headers={
        "User-Agent": "ZYROX-Video-Downloader/1.1"})
    total = 0
    with urllib.request.urlopen(req, timeout=timeout) as r:
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(
                        f"File exceeds {max_bytes // 1_000_000} MB limit")
                f.write(chunk)
    return total
