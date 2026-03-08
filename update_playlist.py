import json
import subprocess

with open("channels.json") as f:
    channels = json.load(f)

playlist = "#EXTM3U\n\n"

for ch in channels:
    try:
        url = subprocess.check_output(
            ["yt-dlp", "-g", ch["source"]],
            text=True
        ).strip()

        playlist += f'#EXTINF:-1 group-title="{ch["group"]}",{ch["name"]}\n'
        playlist += url + "\n\n"

    except:
        pass

with open("playlist.m3u", "w") as f:
    f.write(playlist)
