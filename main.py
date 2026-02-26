"""
TikTok Video Downloader — Download by URL
------------------------------------------
Requirements:
    pip install yt-dlp
    pip install curl_cffi      (recommended — bypasses bot detection)

Optional (for guaranteed mp4):
    Windows : https://ffmpeg.org/download.html  → add ffmpeg/bin to PATH
    Mac     : brew install ffmpeg
    Linux   : sudo apt install ffmpeg

Usage:
    python tiktok_downloader.py
    python tiktok_downloader.py "https://www.tiktok.com/@user/video/123..."
"""

import os
import sys
import shutil
import subprocess


# ─────────────────────────────────────────────
#  Auto-install missing packages
# ─────────────────────────────────────────────
def ensure_packages():
    for pip_name, import_name in [("yt-dlp", "yt_dlp"), ("curl_cffi", "curl_cffi")]:
        try:
            __import__(import_name)
        except ImportError:
            print(f"📦 Installing {pip_name} ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "-q"])
            print(f"✔  {pip_name} installed.\n")


ensure_packages()
import yt_dlp  # noqa: E402  (imported after auto-install)


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def has_ffmpeg() -> bool:
    """Return True if ffmpeg is on the PATH or in common install locations."""
    if shutil.which("ffmpeg"):
        return True
    for p in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]:
        if os.path.exists(p):
            return True
    return False


def progress_hook(d: dict):
    """Print a clean download progress line."""
    if d["status"] == "downloading":
        pct   = d.get("_percent_str", "?%").strip()
        speed = d.get("_speed_str",   "?").strip()
        eta   = d.get("_eta_str",     "?").strip()
        print(f"\r  ⬇  {pct}  |  speed: {speed}  |  ETA: {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\n  ✔  Download complete → {os.path.basename(d['filename'])}")
    elif d["status"] == "error":
        print("\n  ❌  An error occurred during download.")


# ─────────────────────────────────────────────
#  Core download function
# ─────────────────────────────────────────────
def download_tiktok(url: str, output_dir: str = "tiktok_downloads") -> bool:
    """
    Download a single TikTok video.

    Args:
        url        : Full TikTok video URL.
        output_dir : Folder where the video will be saved.

    Returns:
        True on success, False on failure.
    """
    os.makedirs(output_dir, exist_ok=True)

    ffmpeg_ok = has_ffmpeg()
    if ffmpeg_ok:
        print("✔  ffmpeg detected — output will be remuxed to mp4.\n")
        fmt = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[ext=mp4]+bestaudio/"
            "bestvideo+bestaudio/best"
        )
        postprocessors = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    else:
        print("⚠️  ffmpeg not found — downloading best pre-muxed mp4.\n")
        fmt            = "best[ext=mp4]/best"
        postprocessors = []

    opts = {
        # Save as:  output_dir/<uploader>/<title>.mp4
        "outtmpl"            : os.path.join(output_dir, "%(uploader)s", "%(title)s.%(ext)s"),
        "format"             : fmt,
        "merge_output_format": "mp4",
        "nooverwrites"       : True,
        "quiet"              : False,
        "no_warnings"        : False,
        "progress_hooks"     : [progress_hook],

        # ── TikTok anti-bot headers ──────────────────────────
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer"         : "https://www.tiktok.com/",
            "Accept-Language" : "en-US,en;q=0.9",
        },

        # ── Cookie hint (optional — see tip below) ───────────
        # "cookiesfrombrowser": ("chrome",),   # ← uncomment to use Chrome cookies
        # "cookiefile"        : "cookies.txt", # ← or use a Netscape-format cookies file
    }

    # Use curl_cffi browser impersonation if available (best TikTok bypass)
    try:
        from yt_dlp.networking.impersonate import ImpersonateTarget
        opts["impersonate"] = ImpersonateTarget("chrome", "124")
        print("✔  curl_cffi impersonation enabled (Chrome 124).\n")
    except Exception:
        pass

    if postprocessors:
        opts["postprocessors"] = postprocessors

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info     = ydl.extract_info(url, download=True)
            uploader = info.get("uploader", "unknown") if info else "unknown"
            saved_to = os.path.abspath(os.path.join(output_dir, uploader))
            print(f"\n✅  Video saved to: {saved_to}")
            return True

        except yt_dlp.utils.DownloadError as exc:
            print(f"\n❌  Download failed: {exc}")
            _print_tips()
            return False


# ─────────────────────────────────────────────
#  Troubleshooting tips
# ─────────────────────────────────────────────
def _print_tips():
    print("\n💡  Troubleshooting tips:")
    print("  1. Make sure the video is public.")
    print("  2. Update yt-dlp          →  pip install -U yt-dlp")
    print("  3. Install curl_cffi      →  pip install curl_cffi")
    print("  4. Install ffmpeg for mp4 →  https://ffmpeg.org/download.html")
    print("  5. Try with browser cookies (uncomment 'cookiesfrombrowser' in the script).")
    print("  6. Some regions require a VPN.\n")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
def main():
    print("=" * 56)
    print("        🎵  TikTok Video Downloader by URL  🎵")
    print("=" * 56)

    # Accept URL as CLI argument  or  prompt interactively
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        print("\nPaste the full TikTok video URL below.")
        print("Example: https://www.tiktok.com/@username/video/123...\n")
        url = input("🔗  Video URL: ").strip()

    if not url:
        print("❌  No URL provided. Exiting.")
        sys.exit(1)

    if not url.startswith("http"):
        print("❌  Invalid URL — must start with 'https://'")
        sys.exit(1)

    print()
    download_tiktok(url)


if __name__ == "__main__":
    main()