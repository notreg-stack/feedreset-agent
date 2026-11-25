import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction

SCRIPTS = Path(__file__).resolve().parents[1]/"skills/feedreset/scripts"
sys.path.insert(0, str(SCRIPTS))
import feedreset as tool
from intentional import derive
from progress import exposure_change, progress


def post(i, focus="memes", merit="low-value"):
    return {"id":str(i), "label":"Fictional post "+str(i), "creator":"demo", "focus":focus,
            "topics":[focus], "merit":merit, "suggest":"reduce" if merit=="low-value" else "encourage",
            "reason":"Repeated gag." if merit=="low-value" else "A primary measurement is demonstrated."}


def good(i):
    return post(i, "technical-demonstrations", "technical-depth")


class IntentionalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/"demo.db"
        self.db = tool.database(self.path)
        self.addCleanup(self.db.close)
        self.scope = "youtube/demo"

    def audit(self, scope, name, day, items, surface="recommendations", device="iphone"):
        tool.ingest(self.db, scope, {"sample":name,"day":day,"surface":surface,"feed":"Home","device":device,"items":items})

    def curate(self, sample, scope=None):
        self.db.commit()
        net, alias = (scope or self.scope).split("/")
        cmd = [sys.executable,str(SCRIPTS/"feedreset.py"),"--db",str(self.path),"--network",net,
               "--account",alias,"curate",sample]
        return json.loads(subprocess.check_output(cmd,text=True))

    def test_autonomous_proposal_uses_substance_preserves_choices_and_distinguishes_opens(self):
        history = [dict(post(1,"jig calibration","technical-depth"),entry="user-opened"),
                   dict(post(2,"luxury speculation","technical-depth"),entry="autoplay"),
                   dict(post(3),entry="user-opened"),dict(post(4),entry="autoplay")]
        self.audit(self.scope,"h","2026-01-01",history,"history")
        self.audit(self.scope,"old","2025-11-01",[post(6,"stale seed","technical-depth")],"history")
        self.audit(self.scope,"feed","2026-01-02",[post(i) for i in range(20)])
        tool.put_policy(self.db,self.scope,{"keep_topics":["all-football"],"protect":["my-friend"]})
        result = self.curate("feed")
        policy = result["policy"]
        self.assertEqual([v["focus"] for v in result["history_directions"]], ["jig calibration"])
        self.assertEqual(result["user_opened_unwanted"], {"memes":1})
        self.assertNotIn("all-football",policy["reduce"])
        self.assertEqual(policy["protect"], ["my-friend"])
        self.assertEqual(len(result["plan"]["pending"]),20)
        self.assertEqual(policy["replacements"][0]["origin"],"history")
        brief = result["rebuild_proposal"]
        self.assertEqual(brief["minimum_target_slots"],19)
        self.assertEqual(sum(r["proposed_slots"] for r in brief["source_priorities"]),19)
        self.assertEqual(brief["source_priorities"][0]["focus"],"jig calibration")
        self.assertEqual(self.curate("feed")["policy"],policy)

    def test_unchanged_substance_and_unknowns_cannot_manufacture_reorientation(self):
        policy = {"reduce":["memes"],"encourage":["technical-demonstrations"],"keep_topics":[],"protect":[]}
        after = [good(i+100) for i in range(20)]
        self.assertEqual(exposure_change([good(i) for i in range(20)],after,policy),(0,1))
        before = [post(i) for i in range(19)] + [dict(post(19),merit="unknown")]
        self.assertEqual(exposure_change(before,after,policy),(Fraction(19,20),1))
        repeated_ids = [good(i) for i in range(20)]
        self.assertEqual(exposure_change(before,repeated_ids,policy)[0],0)

    def test_four_scope_target_and_behavior_have_independent_denominators(self):
        scopes = [n+"/demo" for n in tool.NETWORKS]
        for scope in scopes:
            self.audit(scope,"base","2026-01-01",[post(i) for i in range(20)])
            self.curate("base",scope)
            self.audit(scope,"day2","2026-01-02",[good(i+100) for i in range(19)]+[post(19)])
            self.audit(scope,"h2","2026-01-02",[dict(good(1),entry="user-opened"),dict(post(2),entry="autoplay"),
                                                dict(post(3),entry="unknown")],"history")
        result = progress(self.db,scopes,"2026-01-02")
        self.assertTrue(result["covers_all_four_networks"])
        self.assertTrue(result["sample_target_met_for_requested_scopes"])
        self.assertEqual(result["reoriented_pct_for_requested_scopes"],95)
        self.assertEqual(result["accounts"][0]["opened_on_day"]["user_opened"],1)
        self.assertEqual(result["accounts"][0]["opened_on_day"]["unwanted"],0)
        self.assertEqual(result["accounts"][0]["opened_on_day"]["other_or_unknown_entry"],2)
        self.assertIsNone(result["accounts"][0]["opened_baseline"]["aligned_pct"])
        self.curate("day2",scopes[0])
        self.assertEqual(progress(self.db,scopes,"2026-01-02")["accounts"][0]["baseline_day"],"2026-01-01")
        self.assertIsNone(progress(self.db,scopes+["youtube/absent"],"2026-01-02")["sample_target_met_for_requested_scopes"])

    def test_regression_with_new_ids_detects_the_returning_topic(self):
        self.audit(self.scope,"base","2026-01-01",[post(i) for i in range(20)])
        self.curate("base")
        self.audit(self.scope,"lift","2026-01-02",[good(i+100) for i in range(20)])
        self.audit(self.scope,"drift","2026-01-03",[good(i+200) for i in range(15)]+[post(i+300) for i in range(5)])
        row = progress(self.db,[self.scope],"2026-01-03")["accounts"][0]
        self.assertEqual(row["change_since_yesterday_pp"],-25)
        self.assertEqual(row["unwanted_topics_growing_pp"],{"memes":25})

    def test_no_credit_for_wrong_device_discovery_or_tiny_sample(self):
        self.audit(self.scope,"base","2026-01-01",[post(i) for i in range(20)])
        self.curate("base")
        self.audit(self.scope,"desktop","2026-01-02",[good(i) for i in range(20)],device="desktop")
        self.audit(self.scope,"search","2026-01-02",[good(i) for i in range(20)],surface="discovery")
        self.assertEqual(progress(self.db,[self.scope],"2026-01-02")["accounts"][0]["status"],"missing_comparable_sample")
        self.audit(self.scope,"phone","2026-01-02",[good(100)])
        result = progress(self.db,[self.scope],"2026-01-02")
        self.assertEqual(result["accounts"][0]["status"],"provisional_small_sample")
        self.assertIsNone(result["reoriented_pct_for_requested_scopes"])

    def test_editorial_seed_is_labeled_and_owner_replacement_wins(self):
        p, evidence = derive(self.db,self.scope,None,[post(1)],"2026-01-01")
        self.assertFalse(evidence["history_directions"])
        self.assertEqual(p["replacements"][0]["origin"],"editorial")
        from questionnaire import apply_answers, menu
        changed = apply_answers(p,menu("youtube",[]),[],[],[],[],[("memes","woodworking","build a shelf")])
        revised, _ = derive(self.db,self.scope,changed,[post(2)],"2026-01-02")
        self.assertEqual(revised["replacements"],[{"reduce":"memes","cultivate":"woodworking","practice":"build a shelf"}])

    def test_recurrence_flags_prior_action_without_double_counting(self):
        self.audit(self.scope,"base","2026-01-01",[post(1)])
        first = self.curate("base")
        from types import SimpleNamespace
        action = first["plan"]["pending"][0]["id"]
        tool.record(self.db,self.scope,SimpleNamespace(sample="base", reset_request=None, action=action,
                                                      outcome="verified",evidence="Fictional readback"))
        self.audit(self.scope,"later","2026-01-02",[post(1)])
        later = tool.plan(self.db,self.scope,"later")
        self.assertFalse(later["pending"])
        self.assertEqual(later["resurfaced"][0]["prior_outcome"],"verified")
