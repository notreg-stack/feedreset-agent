#!/usr/bin/env python3
"""Extract a bounded, local evidence sample from YouTube Takeout watch-history.json."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit


def extract(rows, limit):
    if not isinstance(rows, list) or limit < 1:
        raise ValueError("Expected a watch-history.json array and a positive limit")
    candidates = []
    unreadable = 0
    for row in rows:
        try:
            url = urlsplit(row.get("titleUrl", ""))
            if url.hostname not in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
                raise ValueError()
            video = parse_qs(url.query).get("v", [""])[0]
            title = row.get("title")
            when = datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
            if not when.tzinfo or not video or not isinstance(title, str) or not title.strip():
                raise ValueError()
            subtitles = row.get("subtitles") or []
            byline = subtitles[0].get("name", "") if subtitles and isinstance(subtitles[0], dict) else ""
            candidates.append((when, video, title, byline))
        except (AttributeError, KeyError, IndexError, TypeError, ValueError):
            unreadable += 1
    seen, items = set(), []
    for when, video, title, byline in sorted(candidates, key=lambda row: row[0], reverse=True):
        if video in seen:
            continue
        seen.add(video)
        items.append({"id": video, "label": title, "byline": byline,
                      "observed_at": when.astimezone(timezone.utc).isoformat(),
                      "url": "https://www.youtube.com/watch?v=" + video})
        if len(items) == limit:
            break
    return {"network": "youtube", "surface": "history", "unreadable_rows_in_export": unreadable,
            "sampled_distinct_videos": len(items), "items": items}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("history", type=Path)
    p.add_argument("--limit", type=int, default=20)
    a = p.parse_args()
    try:
        result = extract(json.loads(a.history.read_text(encoding="utf-8")), a.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        sys.exit(f"feedreset: {error}")


if __name__ == "__main__":
    main()
