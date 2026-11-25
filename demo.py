#!/usr/bin/env python3
"""Fictional four-network reconstruction. Runs offline in a temporary database."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

SCRIPTS = Path(__file__).resolve().parent/"skills/feedreset/scripts"
NETWORKS = {"instagram":"Reels", "youtube":"Home", "tiktok":"For You", "x":"For you"}


def item(i, useful, phase):
    if useful:
        return {"id": f"{phase}-detail-{i}", "label": f"Workshop case {i}: finding the cause of a defect",
                "focus":"production engineering", "topics":["technical-demonstrations"], "suggest":"encourage",
                "merit":"technical-depth", "reason":"Shows a diagnosed defect, the intervention and a measured result.",
                "creator":f"demo-workshop-{i % 3}"}
    tag = ("memes", "all-football", "viral-entertainment", "general-humor", "all-politics")[i % 5]
    return {"id":f"{phase}-teaser-{i}", "label":f"Demo {tag} clip {i}", "focus":tag, "topics":[tag],
            "suggest":"reduce","merit":"low-value","reason":"Recycles a teaser with no new information or practical use."}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp)/"demo.db")
        print("Fictional four-network audit. No accounts, online search or platform actions.")
        for net, feed in NETWORKS.items():
            def run(*args, data=None):
                cmd = [sys.executable, str(SCRIPTS/"feedreset.py"), "--db", db, "--network",net,"--account","personal",*args]
                return json.loads(subprocess.check_output(cmd, input=json.dumps(data), text=True))

            def audit(name, day, surface, items):
                run("audit","-",data={"sample":name,"surface":surface,"device":"iphone","feed":feed,
                                      "items":items,"day":day})
            history = [dict(item(0,False,"h"),entry="user-opened"), dict(item(1,True,"h"),entry="user-opened"),
                       dict(item(2,False,"h"),entry="autoplay")]
            audit("prior-views","2026-01-01","history",history)
            audit("baseline","2026-01-01","recommendations",[item(i,False,"b") for i in range(20)])
            review = run("curate","baseline")
            audit("later","2026-01-02","recommendations",[item(i,i < 19,"n") for i in range(20)])
            audit("later-views","2026-01-02","history",[dict(item(i,True,"h2"),entry="user-opened") for i in range(2)])
            run("curate","later")
            print(f"{net}: proposed {len(review['plan']['pending'])} item controls; "
                  f"history seed: {review['history_directions'][0]['focus']}.")
        cmd = [sys.executable,str(SCRIPTS/"progress.py"),"--db",db,"--day","2026-01-02"]
        result = json.loads(subprocess.check_output(cmd,text=True))
        print(f"Simulated later samples: {result['reoriented_pct_for_requested_scopes']}% reoriented.")
        click = result["accounts"][0]
        print(f"Instagram demo: substantive user opens {click['opened_baseline']['aligned']}/{click['opened_baseline']['user_opened']}"
              f" → {click['opened_on_day']['aligned']}/{click['opened_on_day']['user_opened']}.")
        print("Prepared example data illustrates the metric. Real progress requires fresh account observations.")


if __name__ == "__main__":
    main()
