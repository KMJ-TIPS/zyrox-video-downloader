"""
⚡ ZYROX VIDEO DOWNLOADER — yt-dlp engine
Extract info, build quality menus, download with progress hooks.
Runs blocking calls inside a ThreadPoolExecutor from the handlers.
"""

import os
import time

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled, DownloadError

import config
import utils

MAX_VIDEO_BUTTONS = 6
AUDIO_BITRATES = [320, 192, 128]

_KNOWN_HEIGHTS = (4320, 2880, 2160, 1440, 1080, 720, 480, 360, 240, 144)


def _find_ffmpeg() -> str | None:
    """Prefer the bundled static ffmpeg, then any system ffmpeg."""
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (
        os.path.join(here, "bin", "ffmpeg"),
        os.path.join(here, "bin", "ffmpeg.exe"),
        os.environ.get("FFMPEG_PATH", ""),
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


FFMPEG_PATH = _find_ffmpeg()


def _base_opts() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "socket_timeout": 30,
        "retries": 3,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    if FFMPEG_PATH:
        opts["ffmpeg_location"] = FFMPEG_PATH
    if config.COOKIES_FILE and os.path.exists(config.COOKIES_FILE):
        opts["cookiefile"] = config.COOKIES_FILE
    return opts


def extract_info(url: str) -> dict:
    """Blocking: fetch metadata (title, thumbnail, formats...)."""
    with YoutubeDL({**_base_opts(), "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    if info and "entries" in info:
        info = next((e for e in info["entries"] if e), None)
    if not info:
        raise DownloadError("No downloadable media found at this link")
    return info


def _estimate_size(fmt: dict, duration: float):
    size = fmt.get("filesize") or fmt.get("filesize_approx")
    if not size and fmt.get("tbr") and duration:
        size = float(fmt["tbr"]) * 1000 / 8.0 * duration
    return size


def build_quality_menu(info: dict, max_mb: int = config.MAX_FILESIZE_MB) -> dict:
    """
    Parse formats into button-ready lists.

    Returns:
        {
          "videos": [{"format_id", "label", "size"} ...]  (best → lowest)
          "audios": [{"kbps", "label", "size"} ...]
          "note":   optional note about hidden big options
        }
    """
    duration = info.get("duration") or 0
    max_bytes = max_mb * 1024 * 1024

    # ── video formats, dedupe by height, keep the biggest/known size ──
    by_height: dict[int, dict] = {}
    for f in info.get("formats") or []:
        h = f.get("height")
        if not h or f.get("vcodec") in (None, "none"):
            continue
        f["est_size"] = _estimate_size(f, duration)
        cur = by_height.get(h)
        if cur is None or (f.get("est_size") or 0) > (cur.get("est_size") or 0):
            by_height[h] = f

    heights = sorted(by_height.keys(), reverse=True)
    # only keep sensible tiers
    heights = [h for h in heights if h in _KNOWN_HEIGHTS] or heights

    videos, note = [], ""
    for h in heights:
        f = by_height[h]
        size = f.get("est_size") or 0
        if size and size > max_bytes:
            note = "💡 Some higher qualities were hidden (over 50 MB)"
            continue
        name = utils.quality_name(h)
        label = name if name.endswith("p") else f"{name} • {h}p"
        size_txt = utils.human_size(size)
        videos.append(
            {
                "format_id": f.get("format_id"),
                "label": label,
                "size_txt": size_txt,
                "size": size,
                "height": h,
            }
        )
        if len(videos) >= MAX_VIDEO_BUTTONS:
            break

    if not videos:
        # some sites expose no height info — offer auto best
        videos.append(
            {"format_id": None, "label": "BEST QUALITY • AUTO", "size_txt": "—", "size": 0, "height": 0}
        )

    # ── mp3 options (estimated from duration) ──
    audios = []
    for kbps in AUDIO_BITRATES:
        size = duration * kbps * 1000 / 8.0 if duration else 0
        audios.append(
            {
                "kbps": kbps,
                "label": f"MP3 • {kbps} KBPS",
                "size_txt": utils.human_size(size),
                "size": size,
            }
        )

    return {"videos": videos, "audios": audios, "note": note}


def download(
    url: str,
    mode: str,
    format_id=None,
    audio_kbps: int = 320,
    progress_hook=None,
    cancel_check=None,
) -> tuple[str, dict]:
    """
    Blocking download. Returns (filepath, info).

    mode: "video" | "audio"
    Raises DownloadCancelled when cancel_check() returns True.
    """
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

    if mode == "audio":
        opts = {
            **_base_opts(),
            "format": "bestaudio/best",
            "writethumbnail": True,
            "outtmpl": os.path.join(config.DOWNLOAD_DIR, "%(extractor_key)s_%(id)s.%(ext)s"),
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": str(audio_kbps)},
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
        }
    else:
        opts = {
            **_base_opts(),
            "format": f"{format_id}+bestaudio/best" if format_id else "bestvideo*+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(config.DOWNLOAD_DIR, "%(extractor_key)s_%(id)s.%(ext)s"),
        }

    hooks = []
    if progress_hook:
        hooks.append(progress_hook)

    def _hook(d):
        if cancel_check and cancel_check():
            raise DownloadCancelled()
        for h in hooks:
            h(d)

    opts["progress_hooks"] = [_hook]

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info and "entries" in info:
            info = next((e for e in info["entries"] if e), None)
        rd = (info or {}).get("requested_downloads") or []
        if rd and rd[0].get("filepath"):
            return rd[0]["filepath"], info

    # fallback: newest file in download dir
    files = [os.path.join(config.DOWNLOAD_DIR, f) for f in os.listdir(config.DOWNLOAD_DIR)]
    if files:
        return max(files, key=os.path.getmtime), info or {}
    raise DownloadError("Download finished but file was not found")


def find_cover_art(info: dict) -> str | None:
    """If a thumbnail file was downloaded next to the audio, return its path."""
    rd = (info or {}).get("requested_downloads") or []
    if rd:
        thumb = rd[0].get("filepath")
        if thumb:
            base, _ = os.path.splitext(thumb)
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                if os.path.exists(base + ext):
                    return base + ext
    return None


class DownloadCancelledByUser(Exception):
    """Raised internally when user presses CANCEL."""
