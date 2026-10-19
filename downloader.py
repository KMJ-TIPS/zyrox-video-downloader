"""
⚡ ZYROX VIDEO DOWNLOADER — yt-dlp engine
Extract info, build quality menus, download with progress hooks.
Runs blocking calls inside a ThreadPoolExecutor from the handlers.
"""

import base64
import os
import time

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled, DownloadError

import config
import cookies as cookie_store
import utils

MAX_VIDEO_BUTTONS = 6
AUDIO_BITRATES = [320, 192, 128]

_KNOWN_HEIGHTS = (4320, 2880, 2160, 1440, 1080, 720, 480, 360, 240, 144)


def _find_ffmpeg() -> str | None:
    """Prefer the bundled static ffmpeg, then imageio-ffmpeg (pip),
    then any system ffmpeg. The imageio fallback keeps MP3/merge working
    on hosts without a bundled bin/ffmpeg (e.g. Vercel file deploys)."""
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
    try:
        import imageio_ffmpeg  # pip: imageio-ffmpeg (bundles an ffmpeg binary)
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass
    return None


FFMPEG_PATH = _find_ffmpeg()


_VISITOR_DATA: str | None = None


def _visitor_data() -> str:
    """Per-process anonymous visitor ID for Innertube requests.

    GVS PO tokens (needed for SABR streaming URLs) require visitor_data,
    which normally comes from the YouTube webpage — but the webpage is
    the most-blocked endpoint (429 / bot-check) and is skipped. A fresh
    random visitor ID in the standard visitorData protobuf shape
    (field 1, 11 random bytes) works as an anonymous client identifier.
    """
    global _VISITOR_DATA
    if _VISITOR_DATA is None:
        _VISITOR_DATA = base64.urlsafe_b64encode(b"\n\x0b" + os.urandom(11)).decode()
    return _VISITOR_DATA


def _extractor_args(clients: list[str] | None = None, use_pot: bool | None = None) -> dict:
    """YouTube anti-bot configuration: clients + PO-token provider.

    clients : override player client list (fallback attempts)
    use_pot : force PO tokens on/off (None = auto: skip when cookies active)
    """
    if use_pot is None:
        use_pot = bool(config.POT_SERVER_URL) and not cookie_store.active_path()
    effective = clients or list(config.YOUTUBE_CLIENTS)
    args = {
        "youtube": {
            "player_client": effective,
            # Skip the webpage fetch: it is the most-blocked endpoint
            # (429 / bot-check from datacenter IPs) and gates the whole
            # extract. Title/thumbnail/duration come from the player API.
            "player_skip": ["webpage"],
            # Anonymous visitor ID — required for GVS PO tokens (SABR).
            "visitor_data": [_visitor_data()],
        }
    }
    if use_pot and config.FETCH_POT in ("always", "auto", "never"):
        args["youtube"]["fetch_pot"] = [config.FETCH_POT]
    elif not use_pot:
        args["youtube"]["fetch_pot"] = ["never"]
    if use_pot and config.POT_SERVER_URL:
        args["youtubepot-bgutilhttp"] = {"base_url": [config.POT_SERVER_URL]}
    return args


def _base_opts(clients: list[str] | None = None, use_pot: bool | None = None) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "socket_timeout": 30,
        "retries": 3,
        "extractor_args": _extractor_args(clients, use_pot),
    }
    # TLS fingerprint impersonation (needs pip: curl_cffi). Python's
    # default TLS fingerprint is a strong bot signal; impersonating a
    # real browser removes it. Skipped silently if curl_cffi is absent.
    # NOTE: yt-dlp's Python API needs an ImpersonateTarget object — a
    # plain string ("chrome") raises AssertionError in YoutubeDL.__init__.
    try:
        import curl_cffi  # noqa: F401
        from yt_dlp.networking.impersonate import ImpersonateTarget
        opts["impersonate"] = ImpersonateTarget.from_str("chrome")
    except Exception:
        pass
    if config.YTDLP_PROXY:
        opts["proxy"] = config.YTDLP_PROXY
    if FFMPEG_PATH:
        opts["ffmpeg_location"] = FFMPEG_PATH
    cookie_path = cookie_store.active_path()
    if cookie_path and os.path.exists(cookie_path):
        opts["cookiefile"] = cookie_path
    return opts


def is_botcheck_error(err_text: str) -> bool:
    """True when YouTube's datacenter-IP bot wall is the cause."""
    low = (err_text or "").lower()
    return "sign in to confirm" in low or "not a bot" in low


# Fallback chains when the primary attempt hits the bot-check wall.
# WEB FIRST: the web client accepts the PO token and returns a player
# response; tv gets bot-checked even with a token. Embedded clients
# face less scrutiny than the main web client.
_RETRY_NO_POT = ["web", "web_safari", "mweb", "web_embedded", "tv_embedded", "tv"]
_RETRY_EXOTIC = ["ios", "tv_simply", "android_vr", "android", "web"]


def extract_info(url: str) -> dict:
    """Blocking: fetch metadata (title, thumbnail, formats...).

    On YouTube bot-check walls it retries automatically:
      1. normal attempt (PO tokens per config, cookies if installed)
      2. no PO tokens + alternate clients
      3. exotic clients without PO tokens
    """
    strategies = [
        {},
        {"clients": _RETRY_NO_POT, "use_pot": False},
        {"clients": _RETRY_EXOTIC, "use_pot": False},
    ]
    last_err: str | None = None
    for extra in strategies:
        try:
            with YoutubeDL({**_base_opts(**extra), "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            if info and "entries" in info:
                entries = [e for e in (info.get("entries") or []) if e]
                if not entries:
                    # Empty playlist (e.g. blocked/removed video) — never
                    # return None: callers would crash on None.get().
                    raise DownloadError("No downloadable media found at this link")
                info = entries[0]
            if not info:
                raise DownloadError("No downloadable media found at this link")
            return info
        except (DownloadCancelled, KeyboardInterrupt):
            raise
        except DownloadError as e:
            last_err = str(e)
            if not is_botcheck_error(last_err):
                raise
            log_retry(url, extra)
            # Brief pause: hammering the same IP with instant retries
            # trips the rate limiter harder. A short gap lets a
            # transient 429 clear before the next client tries.
            time.sleep(2)
            continue
    raise DownloadError(last_err or "Extraction failed")


def log_retry(url: str, extra: dict) -> None:
    tag = ",".join(extra.get("clients") or config.YOUTUBE_CLIENTS)
    print(f"[zyrox] bot-check on {url} → retrying with clients=[{tag}] pot={extra.get('use_pot')}")


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
    if not info:
        return {"videos": [{"format_id": None, "label": "BEST QUALITY • AUTO", "size_txt": "—", "size": 0, "height": 0}],
                "audios": [{"kbps": k, "label": f"MP3 • {k} KBPS", "size_txt": "—", "size": 0} for k in AUDIO_BITRATES],
                "note": ""}
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

    attempts = [
        {},
        {"clients": _RETRY_NO_POT, "use_pot": False},
        {"clients": _RETRY_EXOTIC, "use_pot": False},
    ]
    last_err: Exception | None = None
    for idx, extra in enumerate(attempts):
        is_last = idx == len(attempts) - 1
        try:
            with YoutubeDL({**opts, **_base_opts(**extra)}) as ydl:
                info = ydl.extract_info(url, download=True)
            if info and "entries" in info:
                entries = [e for e in (info.get("entries") or []) if e]
                info = entries[0] if entries else None
            rd = (info or {}).get("requested_downloads") or []
            if rd and rd[0].get("filepath"):
                return rd[0]["filepath"], info
            break
        except (DownloadCancelled, KeyboardInterrupt):
            raise
        except DownloadError as e:
            last_err = e
            if not is_botcheck_error(str(e)) or is_last:
                raise
            log_retry(url, extra)
            time.sleep(2)
            continue

    # fallback: newest file in download dir
    files = [os.path.join(config.DOWNLOAD_DIR, f) for f in os.listdir(config.DOWNLOAD_DIR)]
    if files:
        return max(files, key=os.path.getmtime), info or {}
    raise last_err or DownloadError("Download finished but file was not found")


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
