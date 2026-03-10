import json
from urllib.request import Request, urlopen

CHANNELS_FILE = "channels.json"
PLAYLIST_FILE = "playlist.m3u"


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def import_playlist(url: str, default_group: str):
    text = fetch_text(url)
    imported = []

    current_name = None
    current_group = default_group

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            current_name = "Unknown"
            current_group = default_group

            if 'group-title="' in line:
                try:
                    current_group = line.split('group-title="', 1)[1].split('"', 1)[0]
                except Exception:
                    current_group = default_group

            if "," in line:
                current_name = line.rsplit(",", 1)[1].strip()

        elif line.startswith("http://") or line.startswith("https://"):
            imported.append((current_name or "Unknown", current_group, line))

    return imported


with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
    channels = json.load(f)

playlist_lines = ["#EXTM3U"]
seen = set()

for ch in channels:
    if not ch.get("enabled", True):
        continue

    if ch.get("type") == "playlist":
        try:
            imported = import_playlist(ch["source"], ch.get("group", "Imported"))

            for name, group, url in imported:
                key = (name.strip().lower(), url.strip())
                if key in seen:
                    continue
                seen.add(key)

                playlist_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
                playlist_lines.append(url)

        except Exception as e:
            print(f"Failed importing playlist {ch.get('name', 'Unknown')}: {e}")

    else:
        name = ch["name"]
        group = ch.get("group", "Other")
        url = ch["source"]

        key = (name.strip().lower(), url.strip())
        if key in seen:
            continue
        seen.add(key)

        playlist_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
        playlist_lines.append(url)

with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines) + "\n")

print(f"Wrote {len(playlist_lines)//2} channel entries to {PLAYLIST_FILE}")
