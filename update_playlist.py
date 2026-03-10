import json
from urllib.request import Request, urlopen

CHANNELS_FILE = "channels.json"
PLAYLIST_FILE = "playlist.m3u"


def fetch_text(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    with urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def parse_m3u_playlist(text: str, default_group: str):
    channels = []
    current_name = None
    current_group = default_group

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            current_group = default_group
            current_name = "Unknown"

            if 'group-title="' in line:
                try:
                    current_group = line.split('group-title="', 1)[1].split('"', 1)[0]
                except Exception:
                    current_group = default_group

            if "," in line:
                current_name = line.rsplit(",", 1)[1].strip()

        elif line.startswith("http://") or line.startswith("https://"):
            channels.append({
                "name": current_name or "Unknown",
                "group": current_group or default_group,
                "source": line
            })

    return channels


def is_reasonable_stream(url: str) -> bool:
    bad_words = [
        ".mpd",
        "drm",
        "license",
        "widevine"
    ]
    lowered = url.lower()
    return not any(word in lowered for word in bad_words)


def dedupe_channels(channels):
    seen = set()
    result = []

    for ch in channels:
        key = (
            ch["name"].strip().lower(),
            ch["source"].strip()
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(ch)

    return result


def sort_channels(channels):
    return sorted(
        channels,
        key=lambda ch: (
            ch.get("group", "").lower(),
            ch.get("name", "").lower()
        )
    )


def main():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    all_channels = []

    for item in config:
        if not item.get("enabled", True):
            continue

        item_type = item.get("type", "channel")
        group = item.get("group", "Other")

        if item_type == "playlist":
            try:
                print(f"Importing playlist: {item['name']}")
                text = fetch_text(item["source"])
                imported = parse_m3u_playlist(text, group)

                for ch in imported:
                    if is_reasonable_stream(ch["source"]):
                        all_channels.append(ch)

                print(f"Imported {len(imported)} channels from {item['name']}")
            except Exception as e:
                print(f"Failed importing {item['name']}: {e}")

        else:
            source = item["source"]
            if is_reasonable_stream(source):
                all_channels.append({
                    "name": item["name"],
                    "group": group,
                    "source": source
                })

    all_channels = dedupe_channels(all_channels)
    all_channels = sort_channels(all_channels)

    lines = ["#EXTM3U"]

    for ch in all_channels:
        lines.append(f'#EXTINF:-1 group-title="{ch["group"]}",{ch["name"]}')
        lines.append(ch["source"])

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {len(all_channels)} channels to {PLAYLIST_FILE}")


if __name__ == "__main__":
    main()
