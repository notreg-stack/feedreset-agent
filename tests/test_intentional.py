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

    def test_owner_reference_scores_first_window_and_guides_sourcing(self):
        ref = dict(good(90), focus="mechanics")
        self.audit(self.scope,"library","2026-01-01",[ref,post(91)],surface="discovery")
        with self.assertRaises(ValueError):
            tool.approve(self.db,self.scope,"library",[],True)
        tool.approve(self.db,self.scope,"library",["90"],False)
        items = [dict(ref,id=str(i)) for i in range(19)] + [dict(ref,id="19",merit="unknown"),ref]
        self.audit(self.scope,"run","2026-01-02",items)
        review = self.curate("run")
        score = review["plan"]["reference_score"]
        self.assertEqual((score["aligned_pct"],score["organic_items"],score["items_needed_for_19_of_20"]),(95,20,0))
        self.assertEqual(score["exact_reappearances"],[])
        self.assertEqual(review["rebuild_proposal"]["source_priorities"][0]["example"]["item"],"90")
        tool.put_policy(self.db,self.scope,{"reduce":["mechanics"]})
        self.assertEqual(tool.plan(self.db,self.scope,"run")["reference_score"]["aligned_pct"],0)
        self.assertEqual(tool.reference_score(self.db,"youtube/another",[ref],review["policy"])["status"],"no_approved_examples")

    def test_recurring_channel_requires_distinct_comparable_clips_and_respects_counterevidence(self):
        channel = "UC"+"x"*22
        def clip(i):
            return dict(post(i),source_id=channel)
        self.audit(self.scope,"old","2026-01-01",[clip(0)])
        self.audit(self.scope,"a","2026-03-01",[clip(1)])
        self.audit(self.scope,"seen-again","2026-03-02",[clip(1)])
        self.audit(self.scope,"other-device","2026-03-02",[clip(3)],device="desktop")
        self.assertEqual(self.curate("seen-again")["plan"]["channel_evidence"],{})
        self.audit(self.scope,"b","2026-03-03",[clip(2)])
        result = self.curate("b")["plan"]
        self.assertEqual(set(result["channel_evidence"][channel]),{"1","2"})
        self.assertIn("dont_recommend_channel",[a["control"] for a in result["pending"]])
        self.audit(self.scope,"useful","2026-03-04",[dict(good(9),source_id=channel)],surface="discovery")
        self.audit(self.scope,"c","2026-03-05",[clip(4)])
        self.assertEqual(self.curate("c")["plan"]["channel_evidence"],{})
        tool.approve(self.db,self.scope,"useful",[],True)
        self.assertEqual(tool.plan(self.db,self.scope,"b")["channel_evidence"],{})
        with self.assertRaises(ValueError):
            self.audit(self.scope,"ambiguous","2026-03-05",[dict(post(5),source_id="Demo Display Name")])

    def test_unconfirmed_feedback_can_gain_a_receipt_without_replaying_the_click(self):
        from types import SimpleNamespace
        self.audit(self.scope,"feed","2026-01-01",[post(1)])
        action = self.curate("feed")["plan"]["pending"][0]["id"]
        args = SimpleNamespace(sample="feed",reset_request=None,action=action,
                               outcome="submitted_unconfirmed",evidence="Menu closed")
        tool.record(self.db,self.scope,args)
        plan = tool.plan(self.db,self.scope,"feed")
        self.assertEqual(plan["awaiting_readback"][0]["id"],action)
        self.assertEqual(plan["pending"],[])
        args.outcome, args.evidence = "verified", "Native acknowledgement"
        tool.record(self.db,self.scope,args)
        self.assertEqual(tool.plan(self.db,self.scope,"feed")["awaiting_readback"],[])

    def test_cli_unapprove_and_missing_reference_are_distinct_from_zero_matches(self):
        self.audit(self.scope,"catalog","2026-01-01",[good(7)],surface="discovery")
        self.audit(self.scope,"feed","2026-01-02",[post(1)])
        self.curate("feed")
        cmd = [sys.executable,str(SCRIPTS/"feedreset.py"),"--db",str(self.path),
               "--network","youtube","--account","demo"]
        def run(*args):
            return json.loads(subprocess.check_output(cmd+list(args),text=True))
        run("approve","catalog","--all")
        run("approve","catalog","--items","7")
        score = run("plan","feed")["reference_score"]
        self.assertEqual((score["approved_examples"],score["status"],score["aligned_pct"]),(1,"partial",0))
        self.assertIsNone(score["items_needed_for_19_of_20"])
        self.assertEqual(run("unapprove","7")["removed"],1)
        self.assertIsNone(run("plan","feed")["reference_score"]["aligned_pct"])
