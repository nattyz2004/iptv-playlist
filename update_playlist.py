import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CHANNELS_FILE = "channels.json"
PLAYLIST_FILE = "playlist.m3u"


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as response:
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

        if line.startswith("#EXTINF:"):
            current_name = None
            current_group = default_group

            if "," in line:
                current_name = line.split(",", 1)[1].strip()

            if 'group-title="' in line:
                try:
                    current_group = line.split('group-title="', 1)[1].split('"', 1)[0].strip()
                except Exception:
                    current_group = default_group

        elif line.startswith("http://") or line.startswith("https://"):
            if current_name is None:
                current_name = "Unnamed Channel"

            imported.append(
                {
                    "name": current_name,
                    "group": current_group,
                    "source": line,
                    "enabled": True,
                }
            )
            current_name = None
            current_group = default_group

    return imported


def build_playlist(channels):
    lines = ["#EXTM3U", ""]

    for channel in channels:
        if not channel.get("enabled", True):
            continue

        name = channel["name"]
        group = channel.get("group", "Other")
        source = channel["source"]

        lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
        lines.append(source)

    return "\n".join(lines) + "\n"


def main():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        channels = json.load(f)

    expanded_channels = []

    for channel in channels:
        if not channel.get("enabled", True):
            continue

        if channel.get("type") == "playlist":
            try:
                imported = import_playlist(
                    channel["source"],
                    channel.get("group", "Imported")
                )
                expanded_channels.extend(imported)
                print(f"[OK] Imported playlist: {channel['name']} ({len(imported)} channels)")
            except HTTPError as e:
                print(f"[SKIP] HTTP error importing {channel['name']}: {channel['source']} -> {e.code}")
            except URLError as e:
                print(f"[SKIP] URL error importing {channel['name']}: {channel['source']} -> {e.reason}")
            except Exception as e:
                print(f"[SKIP] Failed importing {channel['name']}: {channel['source']} -> {e}")
        else:
            expanded_channels.append(channel)

    playlist_text = build_playlist(expanded_channels)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write(playlist_text)

    print(f"[DONE] Wrote {PLAYLIST_FILE} with {len(expanded_channels)} channels")


if __name__ == "__main__":
    main()
