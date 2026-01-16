import random
import datetime
import yt_dlp
import os
import logging
from YTC_channels import channel_metadata

# ---------------- LOGGING ----------------
logger = logging.getLogger("yt_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ---------------- COOKIES ----------------
cookies_file_path = 'cookies.txt'
if not os.path.exists(cookies_file_path):
    raise FileNotFoundError(f"Missing cookies file: {cookies_file_path}")

# ---------------- FALLBACK ----------------
FALLBACK_M3U8 = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/refs/heads/main/assets/moose-403.m3u8"

# ---------------- STABLE USER AGENT ----------------
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.6267.70 Safari/537.36"
)

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.youtube.com/"
}

# ---------------- GET LIVE PAGE ----------------
def get_live_watch_url(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"

    ydl_opts = {
        "cookiefile": cookies_file_path,
        "quiet": True,
        "no_warnings": True,
        "force_ipv4": True,
        "http_headers": BASE_HEADERS,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and info.get("is_live"):
                return info.get("webpage_url")
    except Exception as e:
        logger.error(f"Live check failed for {channel_id}: {e}")

    return None

# ---------------- GET HLS STREAM ----------------
def get_stream_url(watch_url):
    ydl_opts = {
        "format": "best[protocol^=m3u8]/best",
        "cookiefile": cookies_file_path,
        "quiet": True,
        "no_warnings": True,
        "force_ipv4": True,
        "http_headers": BASE_HEADERS,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "skip": ["translated_subs"]
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(watch_url, download=False)

            for f in info.get("formats", []):
                if f.get("protocol") == "m3u8_native" and f.get("url"):
                    return f["url"]

    except Exception as e:
        logger.error(f"HLS fetch failed: {e}")

    return None

# ---------------- FORMAT M3U ----------------
def format_live_link(name, logo, link, group):
    return (
        f'#EXTINF:-1 group-title="{group}" tvg-logo="{logo}",{name}\n'
        f'{link}'
    )

# ---------------- SAVE M3U ----------------
def save_m3u_file(data, filename="YT_playlist_YTC.m3u"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Updated: {datetime.datetime.now()}\n")
        for line in data:
            f.write(line + "\n")

    logger.info(f"M3U saved: {filename}")

# ---------------- MAIN ----------------
def main():
    output = []

    for channel_id, meta in channel_metadata.items():
        name = meta.get("channel_name", "Unknown")
        logo = meta.get("channel_logo", "")
        group = meta.get("group_title", "YouTube Live")

        logger.info(f"Checking {name}")

        watch = get_live_watch_url(channel_id)
        if not watch:
            logger.warning(f"{name}: offline → fallback")
            hls = FALLBACK_M3U8
        else:
            hls = get_stream_url(watch) or FALLBACK_M3U8

        output.append(format_live_link(name, logo, hls, group))

    save_m3u_file(output)

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
