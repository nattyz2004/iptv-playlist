import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CHANNELS_FILE = "channels.json"
PLAYLIST_FILE = "playlist.m3u"


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def clean_group(group):
    if not group:
        return ""
    return str(group).strip()


def auto_group(name: str, existing_group: str, source_url: str) -> str:
    group = clean_group(existing_group)
    lower_name = name.lower()
    lower_group = group.lower()
    lower_source = source_url.lower()

    if group and group not in ["Other", "Undefined", "Ungrouped", "General", "Live TV"]:
        return group

    if "pluto" in lower_source:
        return "Pluto TV"
    if "plex" in lower_source:
        return "Plex"
    if "samsung" in lower_source:
        return "Samsung TV Plus"
    if "roku" in lower_source:
        return "Roku"
    if "xumo" in lower_source:
        return "Xumo"
    if "tubi" in lower_source:
        return "Tubi"

    news_keywords = [
        "news", "cnn", "bbc", "reuters", "al jazeera", "euronews", "fox news",
        "sky news", "cbs news", "abc news", "nbc news", "dw", "france 24",
        "cgtn", "trt world", "nhk", "wion", "cna"
    ]
    sports_keywords = [
        "sport", "sports", "espn", "nfl", "nba", "mlb", "nhl", "golf", "tennis",
        "racing", "fight", "mma", "wrestling", "boxing", "soccer", "football"
    ]
    movie_keywords = [
        "movie", "movies", "cinema", "film", "filmrise", "action", "thriller",
        "drama", "romance", "horror", "western", "sci-fi", "fantastic"
    ]
    kids_keywords = [
        "kids", "kid", "cartoon", "nick", "nickelodeon", "disney", "junior",
        "toons", "anime", "cbbc", "cbeebies", "teletubbies", "yu-gi-oh",
        "rugrats", "spongebob"
    ]
    doc_keywords = [
        "documentary", "documentaries", "history", "nature", "science",
        "forensic", "docurama", "pbs", "nasa"
    ]
    music_keywords = [
        "music", "vevo", "radio", "mtv", "vh1", "trace", "clubbing", "pop",
        "rock", "hip hop", "rap", "k-pop"
    ]
    weather_keywords = [
        "weather", "accuweather", "weathernation", "forecast"
    ]

    def has_keyword(keywords):
        text = f"{lower_name} {lower_group}"
        return any(keyword in text for keyword in keywords)

    if has_keyword(news_keywords):
        return "News"
    if has_keyword(sports_keywords):
        return "Sports"
    if has_keyword(movie_keywords):
        return "Movies"
    if has_keyword(kids_keywords):
        return "Kids"
    if has_keyword(doc_keywords):
        return "Documentaries"
    if has_keyword(music_keywords):
        return "Music"
    if has_keyword(weather_keywords):
        return "Weather"

    return "Other"


def import_playlist(url: str, default_group=None):
    text = fetch_text(url)
    imported = []

    current_name = None
    current_group = default_group if default_group else ""

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current_name = None
            current_group = default_group if default_group else ""

            if "," in line:
                current_name = line.split(",", 1)[1].strip()

            if 'group-title="' in line:
                try:
                    current_group = line.split('group-title="', 1)[1].split('"', 1)[0].strip()
                except Exception:
                    current_group = default_group if default_group else ""

        elif line.startswith("http://") or line.startswith("https://"):
            if current_name is None:
                current_name = "Unnamed Channel"

            final_group = auto_group(current_name, current_group, line)

            imported.append(
                {
                    "name": current_name,
                    "group": final_group,
                    "source": line,
                    "enabled": True,
                }
            )
            current_name = None
            current_group = default_group if default_group else ""

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
                imported = import_playlist(channel["source"], None)
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
