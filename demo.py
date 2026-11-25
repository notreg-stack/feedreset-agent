#!/usr/bin/env python3
"""Offline tour. All evidence is fictional and the database is temporary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory() as tmp:
        def run(*args):
            cmd = [sys.executable, str(ROOT/"skills/feedreset/scripts/feedreset.py"),
                   "--db", str(Path(tmp)/"demo.db"), "--network", "youtube", "--account", "demo", *args]
            return json.loads(subprocess.check_output(cmd, text=True))

        audit = run("audit", str(ROOT/"examples/sample.json"))
        print("FeedReset • fictional YouTube Home • offline demo")
        for item in audit["examples"]:
            print(f"  {item['suggest']:10}  {item['label']} — {item['reason']}")
        menu = run("ask", audit["sample"], "--lang", "en")
        print("\nSeen in this feed:")
        for option in menu["observed"]:
            print(f"  {option['code']}  {option['label']} ({option['observed_count']}/{menu['sample_size']})")
        print("Other optional patterns on YouTube:")
        for option in menu["optional_reduce"][:3]:
            print(f"  {option['code']}  {option['label']}")
        print(menu["question"])
        print("Viewer: I miss doing things with my daughter.")
        print("Agent: Do you miss talking together, or making something together?")
        print("Viewer: Cooking together. She wants to make Saturday breakfast with me.")
        goal = "cooking with my daughter"
        run("answer", audit["sample"], "--replace", "transfer rumors", goal, "make Saturday breakfast together",
            "--encourage", "worked examples", "--protect", "my-friend", "--boost-sources", "--repair-youtube-history")
        result = run("plan", audit["sample"])
        print(f"Goal in the original feed: {len(result['replacements'][0]['goal_items_in_sample'])} items.")
        resource = run("save-resource", "transfer rumors", goal,
                       "https://www.jamieoliver.com/recipes/healthy-breakfast-ideas/buddys-one-cup-pancakes/",
                       "Buddy's one-cup pancakes", "Measure the ingredients and mix the batter together.")
        print("Separately sourced example included in this demo:", resource["title"], "—", resource["reason"])
        print(resource["url"])
        print("Current feed:", result["counts"])
        for action in result["pending"]:
            print("  Proposed:", action["control"], "→", action["label"])
        for item in result["reading_queue"]:
            print("  Keep:", item["label"])
        print("No real accounts accessed. No account changes made.")


if __name__ == "__main__":
    main()
