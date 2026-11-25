import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT/"skills/feedreset/scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS/(name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = load("feedreset")
takeout = load("takeout")


class FeedResetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/"state.db"
        self.db = tool.database(self.path)
        self.addCleanup(self.db.close)
        self.sample = json.loads((ROOT/"examples/sample.json").read_text())
        self.choices = json.loads((ROOT/"examples/choices.json").read_text())
        self.scope = "youtube/personal"

    def enroll(self):
        tool.ingest(self.db, self.scope, self.sample)
        tool.put_policy(self.db, self.scope, self.choices)

    def cli(self, *args, network="youtube", account="personal"):
        cmd = [sys.executable, str(SCRIPTS/"feedreset.py"), "--db", str(self.path),
               "--network", network, "--account", account, *args]
        return subprocess.run(cmd, text=True, capture_output=True)

    def test_diagnosis_before_policy(self):
        result = tool.ingest(self.db, self.scope, self.sample)
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["diagnostic_suggestions"]["uncertain"], 2)
        with self.assertRaisesRegex(ValueError, "person's choices"):
            tool.plan(self.db, self.scope, self.sample["sample"])

    def test_protection_and_mixed_source(self):
        self.enroll()
        result = tool.plan(self.db, self.scope, self.sample["sample"])
        self.assertEqual(result["counts"], {"encourage":2, "reduce":1, "uncertain":1, "protect":1})
        self.assertEqual(len(result["reading_queue"]), 2)
        self.assertEqual({a["control"] for a in result["pending"]}, {"less_like_this", "prioritize_source"})
        self.sample["items"][0]["topics"].append("transfer rumors")
        self.sample["sample"] = "second"
        tool.ingest(self.db, self.scope, self.sample)
        result = tool.plan(self.db, self.scope, "second")
        self.assertEqual(result["counts"]["uncertain"], 2)
        self.assertFalse(any(a["control"] == "prioritize_source" for a in result["pending"]))

    def test_history_repair_and_following_are_distinct(self):
        self.sample["surface"] = "history"
        self.enroll()
        actions = tool.plan(self.db, self.scope, self.sample["sample"])["pending"]
        self.assertEqual([a["control"] for a in actions], ["remove_watch_entry"])
        self.choices["repair_youtube_history"] = False
        tool.put_policy(self.db, self.scope, self.choices)
        self.assertEqual(tool.plan(self.db, self.scope, self.sample["sample"])["pending"], [])
        self.sample.update(surface="following", sample="following")
        tool.ingest(self.db, self.scope, self.sample)
        self.assertTrue(all(a["control"] != "less_like_this" for a in tool.plan(self.db, self.scope, "following")["pending"]))

    def test_replay_duplicate_and_mismatched_account(self):
        self.enroll()
        tool.ingest(self.db, self.scope, self.sample)
        self.assertEqual(len(tool.report(self.db, self.scope)["samples"]), 1)
        self.assertIsNone(tool.report(self.db, "youtube/work")["policy"])
        self.sample["items"][0]["label"] = "Different evidence"
        with self.assertRaisesRegex(ValueError, "already used"):
            tool.ingest(self.db, self.scope, self.sample)
        self.sample["items"].append(self.sample["items"][0])
        with self.assertRaisesRegex(ValueError, "Repeated"):
            tool.ingest(self.db, self.scope, self.sample)

    def test_receipts_guided_verified_and_next_sample(self):
        self.enroll()
        self.db.commit()
        sample = self.sample["sample"]
        action = json.loads(self.cli("plan", sample).stdout)["pending"][0]["id"]
        for status, evidence in [("needs_device", "Shown in app"), ("user_reported", "Owner tapped"),
                                 ("verified", "Observed native state"), ("verified", "Observed native state")]:
            result = self.cli("record", sample, action, status, evidence)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.sample["sample"] = "tomorrow"
        tool.ingest(self.db, self.scope, self.sample)
        self.assertNotIn(action, [a["id"] for a in tool.plan(self.db, self.scope, "tomorrow")["pending"]])
        receipts = tool.report(self.db, self.scope)["actions"]
        self.assertEqual([(r["outcome"],r["evidence"]) for r in receipts], [("verified","Observed native state")])

    def test_reset_is_scoped_and_consumed(self):
        for net in tool.NETWORKS:
            scope = net+"/personal"
            tool.ingest(self.db, scope, self.sample)
            tool.put_policy(self.db, scope, {"reduce":["transfer rumors"]})
            if net in ("instagram", "tiktok"):
                index = self.sample["sample"]
                actions = tool.plan(self.db, scope, index, "one-decision")["pending"]
                action = next(a for a in actions if a["control"] == "reset_suggestions")
                self.db.commit()
                result = self.cli("record", index, action["id"], "verified", "Reset acknowledgement observed",
                                  "--reset-request","one-decision", network=net)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(any(a["control"] == "reset_suggestions" for a in
                                     tool.plan(self.db, scope, index, "one-decision")["pending"]))
            else:
                with self.assertRaisesRegex(ValueError, "whole-feed"):
                    tool.plan(self.db, scope, self.sample["sample"], "one-decision")

    def test_personalized_menu_dedupes_and_handles_unlisted_patterns(self):
        self.sample.update(device="iphone", feed="Home")
        self.sample["items"][0]["topics"] = ["wheel building", "wheel building"]
        tool.ingest(self.db, self.scope, self.sample)
        self.db.commit()
        for lang in ("pt", "en"):
            result = self.cli("ask", self.sample["sample"], "--lang", lang)
            self.assertEqual(result.returncode, 0, result.stderr)
            menu = json.loads(result.stdout)
            self.assertEqual(menu["device"], "iphone")
            self.assertEqual(menu["feed"], "Home")
            seen = {o["topic"]:o for o in menu["observed"]}
            self.assertEqual(seen["sports-rumors"]["observed_count"], 2)
            self.assertEqual(seen["wheel building"]["observed_count"], 1)
            self.assertEqual(seen["wheel building"]["examples"][0]["id"], "demo-a")
            self.assertFalse(seen.keys() & {o["topic"] for o in menu["optional_reduce"]})
        self.assertIsNone(tool.get_policy(self.db, self.scope))
        self.sample["device"] = "desktop"
        with self.assertRaisesRegex(ValueError, "another device"):
            tool.ingest(self.db, self.scope, self.sample)

    def test_selection_codes_custom_topics_protection_and_correction(self):
        self.enroll()
        self.db.commit()
        sample = self.sample["sample"]
        menu = json.loads(self.cli("ask", sample).stdout)
        football = next(o["code"] for o in menu["observed"] if o["topic"] == "sports-rumors")
        before = json.loads(self.cli("report").stdout)["policy"]
        self.assertNotEqual(self.cli("answer", sample, "--keep", "O999").returncode, 0)
        self.assertEqual(json.loads(self.cli("report").stdout)["policy"], before)
        result = self.cli("answer", sample, "--keep", football, "--reduce", "hardware shopping", "--encourage", "E1")
        self.assertEqual(result.returncode, 0, result.stderr)
        policy = json.loads(result.stdout)
        self.assertIn("sports-rumors", policy["keep_topics"])
        self.assertNotIn("sports-rumors", policy["reduce"])
        self.assertIn("hardware shopping", policy["reduce"])
        self.assertTrue(policy["boost_sources"])
        self.assertEqual(json.loads(self.cli("plan", sample).stdout)["counts"]["protect"], 2)

    def test_general_menu_has_zero_personal_evidence(self):
        menus = {}
        for net in tool.NETWORKS:
            menu = json.loads(self.cli("ask", network=net).stdout)
            self.assertEqual(menu["sample_size"], 0)
            self.assertEqual(menu["observed"], [])
            menus[net] = [o["topic"] for o in menu["optional_reduce"]]
        self.assertNotEqual(menus["x"], menus["youtube"])
        expanded = json.loads(self.cli("ask", "--all").stdout)
        self.assertGreater(len(expanded["optional_reduce"]), len(menus["youtube"]))
        self.assertIn("all-football", [o["topic"] for o in expanded["optional_reduce"]])

    def test_takeout_recent_distinct_history(self):
        def row(video, date):
            return {"title":"Watched demo", "titleUrl":"https://www.youtube.com/watch?v="+video,
                    "time":date+"T10:00:00Z"}
        result = takeout.extract([row("a","2025-01-01"),{},row("b","2025-01-02"),row("a","2025-01-03")], 2)
        self.assertEqual([i["id"] for i in result["items"]], ["a","b"])
        self.assertEqual(result["surface"], "history")
        self.assertEqual(result["unreadable_rows_in_export"], 1)

    def test_daily_invokes_only_enrolled_accounts(self):
        self.enroll()
        tool.ingest(self.db, "x/unenrolled", self.sample)
        self.db.commit()
        command = [sys.executable, str(SCRIPTS/"daily.py"), "prompt", "--db", str(self.path)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertIn("youtube/personal",result.stdout)
        self.assertNotIn("x/unenrolled",result.stdout)
        fake = Path(self.tmp.name)/"fake-agent"
        fake.write_text("#!/bin/sh\npwd\ncat\nexit 7\n")
        fake.chmod(0o700)
        for agent in ("codex","claude"):
            command[2] = agent
            result = subprocess.run([*command, "--binary",str(fake)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 7)
            self.assertIn(str(SCRIPTS.parent),result.stdout)
            self.assertIn("youtube/personal",result.stdout)
