import json
import subprocess

with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

playlist = "#EXTM3U\n\n"

for ch in channels:
    source = ch["source"]

    if source.endswith(".m3u8"):
        url = source
    else:
        try:
            url = subprocess.check_output(
                ["yt-dlp", "-g", source],
                text=True
            ).strip()
        except Exception:
            continue

    playlist += f'#EXTINF:-1 group-title="{ch["group"]}",{ch["name"]}\n'
    playlist += url + "\n\n"

with open("playlist.m3u", "w", encoding="utf-8") as f:
    f.write(playlist)
