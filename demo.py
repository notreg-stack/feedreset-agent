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
        run("policy", str(ROOT/"examples/choices.json"))
        result = run("plan", audit["sample"])
        print("\nDemo owner: more worked examples, less transfer gossip; keep my friend.")
        print("Current feed:", result["counts"])
        for action in result["pending"]:
            print("  Proposed:", action["control"], "→", action["label"])
        for item in result["reading_queue"]:
            print("  Keep:", item["label"])
        print("No real accounts accessed. No account changes made.")


if __name__ == "__main__":
    main()
