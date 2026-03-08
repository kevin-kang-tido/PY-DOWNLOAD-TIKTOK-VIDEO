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
    python tiktok_downloader.py "https://..." "C:/Videos" "my_video"
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
import yt_dlp  # noqa: E402


# ─────────────────────────────────────────────
#  Default download folder
#  ← Change this to your preferred folder
# ─────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = r"C:\Users\kang\Videos\video-downlaod-tiktok\raw video\py_video"
# Examples:
#   Windows : r"C:\Users\YourName\Videos\TikTok"
#   Mac/Linux: "/home/yourname/Videos/TikTok"


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def has_ffmpeg() -> bool:
    if shutil.which("ffmpeg"):
        return True
    for p in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]:
        if os.path.exists(p):
            return True
    return False


def sanitize_filename(name: str) -> str:
    """Remove characters that are illegal in filenames."""
    illegal = r'\/:*?"<>|'
    for ch in illegal:
        name = name.replace(ch, "_")
    return name.strip()


def progress_hook(d: dict):
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
def download_tiktok(url: str, output_dir: str, custom_name: str = "") -> bool:
    """
    Download a single TikTok video.

    Args:
        url         : Full TikTok video URL.
        output_dir  : Folder where the video will be saved.
        custom_name : Optional custom filename (without extension).
                      Defaults to the video's original title.
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

    # ── Filename template ────────────────────────────────────
    if custom_name:
        safe_name = sanitize_filename(custom_name)
        filename  = f"{safe_name}.%(ext)s"
        print(f"📝  File will be saved as: {safe_name}.mp4\n")
    else:
        filename  = "%(title)s.%(ext)s"
        print("📝  File will be saved with original TikTok title.\n")

    opts = {
        "outtmpl"            : os.path.join(output_dir, filename),
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
            "Referer"        : "https://www.tiktok.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },

        # "cookiesfrombrowser": ("chrome",),   # ← uncomment to use Chrome cookies
        # "cookiefile"        : "cookies.txt", # ← or use a Netscape-format cookies file
    }

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
            ydl.extract_info(url, download=True)
            final_name = f"{sanitize_filename(custom_name)}.mp4" if custom_name else "(original title).mp4"
            print(f"\n✅  Done!  →  {os.path.join(os.path.abspath(output_dir), final_name)}")
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

    # ── 1. Resolve URL ───────────────────────────────────────
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

    # ── 2. Resolve output folder ─────────────────────────────
    if len(sys.argv) > 2:
        output_dir = sys.argv[2].strip()
    else:
        print(f"\n📁  Where should the video be saved?")
        print(f"    Press Enter to use default: {os.path.abspath(DEFAULT_OUTPUT_DIR)}")
        user_path  = input("📂  Output folder (or Enter for default): ").strip()
        output_dir = user_path if user_path else DEFAULT_OUTPUT_DIR

    output_dir = os.path.expandvars(os.path.expanduser(output_dir))

    # ── 3. Resolve custom filename ───────────────────────────
    if len(sys.argv) > 3:
        custom_name = sys.argv[3].strip()
    else:
        print(f"\n✏️   What should the file be named?")
        print(f"    Press Enter to keep the original TikTok title.")
        custom_name = input("📝  File name (without extension, or Enter to skip): ").strip()

    print(f"\n📁  Saving to : {os.path.abspath(output_dir)}")
    if custom_name:
        print(f"📝  File name : {sanitize_filename(custom_name)}.mp4")
    else:
        print(f"📝  File name : (original TikTok title)")
    print()

    download_tiktok(url, output_dir, custom_name)


if __name__ == "__main__":
    main()