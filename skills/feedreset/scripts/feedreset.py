#!/usr/bin/env python3
"""Account-scoped local memory for a personal feed curator. Python 3.9+."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from questionnaire import apply_answers, canonical, menu
from intentional import MERITS, derive, quality_evidence

NETWORKS = ("instagram", "youtube", "tiktok", "x")
KINDS = ("encourage", "reduce", "uncertain")
SURFACES = ("recommendations", "following", "history", "discovery")
OUTCOMES = ("verified", "user_reported", "submitted_unconfirmed", "needs_device", "unavailable")
SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
  scope TEXT, sample TEXT, day TEXT, surface TEXT, data TEXT,
  PRIMARY KEY(scope,sample));
CREATE TABLE IF NOT EXISTS policies (scope TEXT PRIMARY KEY, data TEXT);
CREATE TABLE IF NOT EXISTS contexts (
  scope TEXT, sample TEXT, device TEXT, feed TEXT, PRIMARY KEY(scope,sample));
CREATE TABLE IF NOT EXISTS actions (
  scope TEXT, id TEXT, control TEXT, target TEXT, evidence TEXT, outcome TEXT,
  last_sample TEXT, PRIMARY KEY(scope,id));
CREATE TABLE IF NOT EXISTS resources (
  scope TEXT, trap TEXT, goal TEXT, practice TEXT, url TEXT, title TEXT, reason TEXT,
  PRIMARY KEY(scope,trap,goal,practice,url));
CREATE TABLE IF NOT EXISTS baselines (scope TEXT PRIMARY KEY, sample TEXT);
CREATE TABLE IF NOT EXISTS approved_examples (
  scope TEXT, item TEXT, sample TEXT, focus TEXT, label TEXT, reason TEXT, url TEXT, source_id TEXT,
  PRIMARY KEY(scope,item));
"""

def require(condition, message):
    if not condition:
        raise ValueError(message)


def string(value, field):
    require(isinstance(value, str) and value.strip(), f"Missing or invalid {field}")
    return value.strip()


def norm(s):
    return unicodedata.normalize("NFKC", s.strip()).casefold()


def tags(values, field):
    require(isinstance(values, list), f"{field} must be a list")
    return sorted({norm(string(v, field)) for v in values})


def read_json(path):
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def database(path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def public_link(value):
    url = string(value, "url")
    u = urlsplit(url)
    require(u.scheme == "https" and u.hostname and not u.username and not u.password,
            "Use a public HTTPS link without credentials")
    return url


def normalize_item(value):
    require(isinstance(value, dict), "Each item must be an object")
    item = {k: string(value.get(k), k) for k in ("id", "label", "reason", "suggest")}
    require(item["suggest"] in KINDS, "Invalid suggest value")
    item["topics"] = tags(value.get("topics"), "topics")
    if "focus" in value:
        item["focus"] = canonical(string(value["focus"], "focus"))
        item["topics"] = sorted(set(item["topics"]) | {item["focus"]})
    if "merit" in value:
        require(value["merit"] in (*MERITS, "low-value", "unknown"), "Unknown editorial merit")
        item["merit"] = value["merit"]
    if "entry" in value:
        require(value["entry"] in ("user-opened","autoplay","unknown"), "Unknown history entry provenance")
        item["entry"] = value["entry"]
    item["creator"] = string(value["creator"], "creator") if value.get("creator") else ""
    if value.get("source_id"):
        item["source_id"] = string(value["source_id"], "source_id")
    url = value.get("url", "")
    require(isinstance(url, str), "url must be text")
    item["url"] = public_link(url) if url else ""
    return item


def get_policy(db, scope):
    row = db.execute("SELECT data FROM policies WHERE scope=?", (scope,)).fetchone()
    return json.loads(row["data"]) if row else None


def put_policy(db, scope, raw):
    require(isinstance(raw, dict), "Expected a policy object")
    keys = {"encourage", "reduce", "protect", "keep_topics", "repair_youtube_history", "boost_sources", "replacements"}
    require(set(raw) <= keys, "Unknown policy field")
    policy = {k: sorted({canonical(t) for t in tags(raw.get(k, []), k)})
              for k in ("encourage", "reduce", "keep_topics")}
    policy["protect"] = tags(raw.get("protect", []), "protect")
    policy["protect"] = sorted({name.lstrip("@") for name in policy["protect"]})
    all_topics = policy["encourage"] + policy["reduce"] + policy["keep_topics"]
    require(len(all_topics) == len(set(all_topics)), "Conflicting topic choices")
    repair = raw.get("repair_youtube_history", False)
    require(isinstance(repair, bool), "repair_youtube_history must be true or false")
    require(not repair or scope.startswith("youtube/"), "History repair is specific to YouTube")
    policy["repair_youtube_history"] = repair
    boost = raw.get("boost_sources", False)
    require(isinstance(boost, bool), "boost_sources must be true or false")
    policy["boost_sources"] = boost
    pairs = {}
    replacements = raw.get("replacements", [])
    require(isinstance(replacements, list), "replacements must be a list")
    for pair in replacements:
        require(isinstance(pair, dict), "Expected a replacement object")
        trap = canonical(string(pair.get("reduce"), "reduce"))
        goal = canonical(string(pair.get("cultivate"), "cultivate"))
        require(trap in policy["reduce"] and goal in policy["encourage"], "Replacement conflicts with topic choices")
        require((trap, goal) not in pairs, "Duplicate replacement")
        pairs[trap, goal] = {"reduce": trap, "cultivate": goal, "practice": string(pair.get("practice"), "practice")}
        origin = pair.get("origin", "owner")
        require(origin in ("owner", "history", "editorial"), "Unknown replacement origin")
        if origin != "owner":
            pairs[trap, goal]["origin"] = origin
    policy["replacements"] = list(pairs.values())
    db.execute("INSERT OR REPLACE INTO policies VALUES (?,?)", (scope, json.dumps(policy)))
    return policy


def ingest(db, scope, raw):
    require(isinstance(raw, dict), "Expected a sample object")
    sample, day, surface = [string(raw.get(k), k) for k in ("sample", "day", "surface")]
    require(day == date.fromisoformat(day).isoformat() and day <= date.today().isoformat(),
            "Use the local observation date, YYYY-MM-DD")
    require(surface in SURFACES, "Unknown surface")
    device = raw.get("device", "unknown")
    require(device in ("iphone", "desktop", "other", "unknown"), "Invalid device")
    feed = string(raw.get("feed", surface), "feed")
    require(isinstance(raw.get("items"), list) and raw["items"], "Supply at least one real item")
    items = [normalize_item(i) for i in raw["items"]]
    if scope.startswith("youtube/"):
        require(all(not i.get("source_id") or re.fullmatch(r"UC[A-Za-z0-9_-]{22}", i["source_id"])
                    for i in items), "Use the YouTube channel ID for source_id, or omit it")
    require(len({i["id"] for i in items}) == len(items), "Repeated item id within sample")
    data = json.dumps(items, ensure_ascii=False)
    existing = db.execute("SELECT day,surface,data FROM samples WHERE scope=? AND sample=?",
                          (scope, sample)).fetchone()
    if existing:
        require(tuple(existing) == (day, surface, data), "Sample id already used for different evidence")
        context = db.execute("SELECT device,feed FROM contexts WHERE scope=? AND sample=?", (scope, sample)).fetchone()
        require(context is None or tuple(context) == (device, feed), "Sample id already used for another device or feed")
    else:
        db.execute("INSERT INTO samples VALUES (?,?,?,?,?)", (scope, sample, day, surface, data))
    db.execute("INSERT OR IGNORE INTO contexts VALUES (?,?,?,?)", (scope, sample, device, feed))
    counts = {k: sum(i["suggest"] == k for i in items) for k in KINDS}
    return {"sample": sample, "surface": surface, "device": device, "feed": feed, "total": len(items),
            "diagnostic_suggestions": counts, "examples": [
                {"label": i["label"], "reason": i["reason"], "suggest": i["suggest"]} for i in items]}


def sample_data(db, scope, sample):
    row = db.execute("SELECT * FROM samples WHERE scope=? AND sample=?", (scope, sample)).fetchone()
    require(row is not None, "Unknown sample for this account")
    return row, json.loads(row["data"])


def sample_context(db, scope, row):
    context = db.execute("SELECT device,feed FROM contexts WHERE scope=? AND sample=?", (scope, row["sample"])).fetchone()
    return dict(context) if context else {"device": "unknown", "feed": row["surface"]}


def decision(item, policy):
    if norm(item["creator"]).lstrip("@") in policy["protect"]:
        return "protect"
    if item.get("source_id") and norm(item["source_id"]) in policy["protect"]:
        return "protect"
    topics = {canonical(t) for t in item["topics"]}
    if topics.intersection(policy.get("keep_topics", [])):
        return "protect"
    positive = topics.intersection(canonical(t) for t in policy["encourage"])
    negative = topics.intersection(canonical(t) for t in policy["reduce"])
    if item.get("merit") == "low-value" and item["suggest"] == "reduce":
        return "reduce" if negative else "uncertain"
    if item.get("merit") == "unknown" and positive:
        return "uncertain"
    if positive and not negative:
        return "encourage"
    if negative and not positive:
        return "reduce"
    return "uncertain"


def action_id(control, target):
    return hashlib.sha256(json.dumps([control, target]).encode()).hexdigest()[:24]


def approve(db, scope, sample, ids, all_items):
    row, items = sample_data(db, scope, sample)
    require(row["surface"] == "discovery", "Approve examples from an audited discovery sample")
    chosen = items if all_items else [item for item in items if item["id"] in ids]
    require(chosen and (all_items or len(chosen) == len(set(ids))), "Unknown or empty selection")
    require(all(quality_evidence(i) for i in chosen), "Each example needs a focus and substantive evidence")
    db.executemany("INSERT OR REPLACE INTO approved_examples VALUES (?,?,?,?,?,?,?,?)",
                   [(scope, i["id"], sample, i["focus"], i["label"], i["reason"], i["url"], i.get("source_id"))
                    for i in chosen])
    return {"scope": scope, "approved": [i["id"] for i in chosen]}


def reference_score(db, scope, items, policy):
    examples = list(db.execute("SELECT item,focus FROM approved_examples WHERE scope=?", (scope,)))
    focuses = {row["focus"] for row in examples}
    reference_ids = {row["item"] for row in examples}
    window = items[:20]
    matches = []
    for item in window:
        choice = decision(item, policy)
        reduced = set(item["topics"]).intersection(policy["reduce"])
        if (quality_evidence(item) and item["focus"] in focuses
                and (choice == "protect" or not reduced)):
            matches.append(item["id"])
    status = "complete" if len(window) == 20 else "partial"
    return {"status": status if examples else "no_approved_examples",
            "approved_examples": len(examples), "organic_items": len(window),
            "aligned_items": matches, "aligned_pct": round(100 * len(matches) / len(window), 2) if examples else None,
            "exact_reappearances": [i["id"] for i in window if i["id"] in reference_ids],
            "items_needed_for_19_of_20": 19 - min(19, len(matches)) if examples and len(window) == 20 else None}


def recurring_channels(db, scope, row, items, policy):
    candidates = {i["source_id"] for i in items if i.get("source_id") and decision(i, policy) == "reduce"}
    candidates.difference_update(r["source_id"] for r in db.execute(
        "SELECT DISTINCT source_id FROM approved_examples WHERE scope=?", (scope,)))
    if not candidates:
        return {}
    context = sample_context(db, scope, row)
    since = (date.fromisoformat(row["day"]) - timedelta(days=30)).isoformat()
    samples = db.execute("""
        SELECT s.data,s.surface,c.device,c.feed FROM samples s LEFT JOIN contexts c USING(scope,sample)
        WHERE s.scope=?
          AND s.day>=? AND (s.day, s.rowid) <=
              (SELECT day,rowid FROM samples WHERE scope=? AND sample=?)
        ORDER BY s.day,s.rowid""", (scope, since, scope, row["sample"]))
    evidence = {source: {} for source in candidates}
    mixed = set()
    for sample in samples:
        comparable = (sample["surface"] == "recommendations" and sample["device"] == context["device"]
                      and sample["feed"] == context["feed"])
        for item in json.loads(sample["data"]):
            source = item.get("source_id")
            if source not in candidates:
                continue
            if (item.get("merit") == "low-value" and item["suggest"] == "reduce"
                    and decision(item, policy) == "reduce"):
                if comparable:
                    evidence[source][item["id"]] = item["reason"]
            else:
                mixed.add(source)
    return {source: reasons for source, reasons in sorted(evidence.items())
            if len(reasons) >= 2 and source not in mixed}


def save_resource(db, scope, args):
    policy = get_policy(db, scope) or {}
    trap, goal = canonical(args.trap), canonical(args.goal)
    pair = next((r for r in policy.get("replacements", [])
                 if r["reduce"] == trap and r["cultivate"] == goal), None)
    require(pair is not None, "Choose this replacement in the interview first")
    url, title, reason = public_link(args.url), string(args.title, "title"), string(args.reason, "reason")
    db.execute("INSERT OR REPLACE INTO resources VALUES (?,?,?,?,?,?,?)",
               (scope, trap, goal, pair["practice"], url, title, reason))
    return {"cultivate": goal, "practice": pair["practice"], "url": url, "title": title, "reason": reason}


def replacement_plan(db, scope, policy, items):
    out = []
    for pair in policy.get("replacements", []):
        trap, goal = pair["reduce"], pair["cultivate"]
        traps, useful = [], []
        for item in items:
            topics = {canonical(t) for t in item["topics"]}
            choice = decision(item, policy)
            if trap in topics and choice == "reduce":
                traps.append(item["id"])
            if goal in topics and choice == "encourage":
                useful.append(item["id"])
        rows = db.execute("SELECT url,title,reason FROM resources WHERE scope=? AND trap=? AND goal=? AND practice=? ORDER BY rowid DESC",
                          (scope, trap, goal, pair["practice"]))
        out.append({**pair, "unwanted_items_in_sample": traps, "goal_items_in_sample": useful,
                    "resources_found_separately": [dict(r) for r in rows]})
    return out


def plan(db, scope, sample, reset=False):
    row, items = sample_data(db, scope, sample)
    policy = get_policy(db, scope)
    require(policy is not None, "Diagnose first, then save the person's choices with policy")
    network = scope.split("/", 1)[0]
    counts = dict.fromkeys((*KINDS, "protect"), 0)
    actions, reading = [], []
    source_choices = {}
    for item in items:
        choice = decision(item, policy)
        counts[choice] += 1
        if item["creator"]:
            creator = norm(item["creator"]).lstrip("@")
            source_choices.setdefault(creator, []).append(choice)
        if choice == "encourage":
            reading.append({k: item[k] for k in ("id", "label", "reason", "creator", "url")})
        if choice != "reduce":
            continue
        if row["surface"] == "recommendations":
            control = "less_like_this"
        elif row["surface"] == "history" and network == "youtube" and policy["repair_youtube_history"]:
            control = "remove_watch_entry"
        else:
            continue
        actions.append((control, item["id"], item["label"]))
    if policy["boost_sources"] and row["surface"] != "history":
        for creator, choices in source_choices.items():
            if len(choices) >= 2 and all(choice == "encourage" for choice in choices):
                actions.append(("prioritize_source", creator, creator))
    if reset:
        require(network in ("instagram", "tiktok"), "No supported whole-feed reset for this network")
        require(row["surface"] == "recommendations", "A reset requires a recommendations baseline")
        # Stable across samples. A used reset stays consumed until a new explicit reset request.
        actions.append(("reset_suggestions", reset, "Account-wide recommendation reset"))
    channel_evidence = {}
    if network == "youtube" and row["surface"] == "recommendations":
        channel_evidence = recurring_channels(db, scope, row, items, policy)
        actions.extend(("dont_recommend_channel", source, source) for source in channel_evidence)
    pending, resurfaced, awaiting_readback = [], [], []
    for control, target, label in actions:
        aid = action_id(control, target)
        existing = db.execute("SELECT outcome,last_sample FROM actions WHERE scope=? AND id=?", (scope, aid)).fetchone()
        if existing and existing["outcome"] == "submitted_unconfirmed" and (
                existing["last_sample"] == sample or control != "less_like_this"):
            awaiting_readback.append({"id": aid, "control": control, "target": target})
            continue
        if existing and existing["outcome"] in ("verified", "user_reported"):
            if control == "less_like_this" and existing["last_sample"] != sample:
                prior, _ = sample_data(db, scope, existing["last_sample"])
                if prior["day"] < row["day"]:
                    resurfaced.append({"target": target, "label": label, "prior_outcome": existing["outcome"]})
            continue
        pending.append({"id": aid, "control": control, "target": target, "label": label,
                        "previous_outcome": existing["outcome"] if existing else None})
    return {"scope": scope, "sample": sample, "surface": row["surface"], "counts": counts,
            "reference_score": reference_score(db, scope, items, policy) if row["surface"] == "recommendations" else None,
            "channel_evidence": channel_evidence, "awaiting_readback": awaiting_readback,
            "reading_queue": reading, "pending": pending, "resurfaced": resurfaced,
            "replacements": replacement_plan(db, scope, policy, items)}


def record(db, scope, args):
    actions = plan(db, scope, args.sample, args.reset_request)["pending"]
    action = next((a for a in actions if a["id"] == args.action), None)
    existing = db.execute("SELECT evidence,outcome,last_sample FROM actions WHERE scope=? AND id=?",
                          (scope, args.action)).fetchone()
    evidence = string(args.evidence, "evidence")
    if existing and (existing["evidence"], existing["outcome"]) == (evidence, args.outcome):
        return {"id": args.action, "outcome": args.outcome}
    if (action is None and existing and
            ((existing["outcome"] == "user_reported" and args.outcome == "verified") or
             (existing["outcome"] == "submitted_unconfirmed" and existing["last_sample"] == args.sample
              and args.outcome in ("verified", "user_reported", "needs_device", "unavailable")))):
        db.execute("UPDATE actions SET outcome=?,evidence=? WHERE scope=? AND id=?",
                   (args.outcome, evidence, scope, args.action))
    else:
        require(action is not None, "Action absent from current plan or already completed")
        db.execute("INSERT OR REPLACE INTO actions VALUES (?,?,?,?,?,?,?)",
                   (scope, action["id"], action["control"], action["target"],
                    evidence, args.outcome, args.sample))
    return {"id": args.action, "outcome": args.outcome}


def report(db, scope):
    policy = get_policy(db, scope)
    observations = []
    for row in db.execute("SELECT * FROM samples WHERE scope=? ORDER BY day,rowid", (scope,)):
        items = json.loads(row["data"])
        counts = None if policy is None else {
            k: sum(decision(i, policy) == k for i in items) for k in (*KINDS, "protect")}
        observations.append({"sample": row["sample"], "day": row["day"], "surface": row["surface"],
                             **sample_context(db, scope, row), "n": len(items), "under_current_choices": counts})
    receipts = db.execute("SELECT control,target,outcome,evidence,last_sample FROM actions WHERE scope=? ORDER BY rowid",
                          (scope,))
    return {"scope": scope, "policy": policy, "samples": observations, "actions": [dict(r) for r in receipts]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path.home()/".feedreset"/"state.sqlite3")
    parser.add_argument("--network", required=True, choices=NETWORKS)
    parser.add_argument("--account", required=True, help="Stable account alias on this network")
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("approve", help="Record the owner's chosen discovery examples")
    sub.add_argument("sample")
    group = sub.add_mutually_exclusive_group(required=True)
    group.add_argument("--items", nargs="+")
    group.add_argument("--all", action="store_true")
    commands.add_parser("unapprove", help="Remove items from the private reference set").add_argument("items", nargs="+")
    sub = commands.add_parser("curate", help="Apply the intentional curation profile and learn from audited history")
    sub.add_argument("sample", nargs="?", help="Current organic recommendation sample; first one anchors progress")
    for name in ("audit", "policy"):
        commands.add_parser(name).add_argument("file", help="JSON path, or - for stdin")
    for name in ("ask", "answer"):
        sub = commands.add_parser(name)
        sub.add_argument("sample", nargs="?", help="Omit to use general prompts only")
        if name == "ask":
            sub.add_argument("--lang", choices=("pt","en"), default="pt")
            sub.add_argument("--all", action="store_true", help="Show every optional topic")
        else:
            sub.add_argument("--replace", action="append", nargs=3, default=[], metavar=("TRAP","GOAL","PRACTICE"),
                             help="Link an unwanted pattern to a chosen goal and a concrete off-screen action")
            for field in ("reduce", "encourage", "keep", "protect"):
                sub.add_argument("--"+field, action="extend", nargs="+", default=[])
            for field in ("boost-sources", "repair-youtube-history"):
                sub.add_argument("--"+field, action=argparse.BooleanOptionalAction, default=None)
    for name in ("plan", "record"):
        sub = commands.add_parser(name)
        sub.add_argument("sample")
        sub.add_argument("--reset-request", help="Unique, confirmed one-shot request ID for Instagram/TikTok")
        if name == "record":
            sub.add_argument("action")
            sub.add_argument("outcome", choices=OUTCOMES)
            sub.add_argument("evidence")
    sub = commands.add_parser("save-resource", help="Save a source inspected for a confirmed replacement")
    for field in ("trap", "goal", "url", "title", "reason"):
        sub.add_argument(field)
    commands.add_parser("report")
    args = parser.parse_args()
    scope = args.network + "/" + norm(string(args.account, "account"))
    os.umask(0o077)
    db = database(args.db)
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            if args.command == "audit":
                result = ingest(db, scope, read_json(args.file))
            elif args.command == "approve":
                result = approve(db, scope, args.sample, args.items or [], args.all)
            elif args.command == "unapprove":
                removed = db.executemany("DELETE FROM approved_examples WHERE scope=? AND item=?",
                                         [(scope, item) for item in set(args.items)])
                result = {"scope": scope, "removed": removed.rowcount}
            elif args.command == "policy":
                result = put_policy(db, scope, read_json(args.file))
            elif args.command == "curate":
                day, items = date.today().isoformat(), []
                if args.sample:
                    row, items = sample_data(db, scope, args.sample)
                    require(row["surface"] == "recommendations", "Use an organic recommendation sample as baseline")
                    context = sample_context(db, scope, row)
                    require(context["device"] != "unknown" and context["feed"] != "recommendations",
                            "Name the actual device and feed before anchoring the baseline")
                    day = row["day"]
                    db.execute("INSERT OR IGNORE INTO baselines VALUES (?,?)", (scope, args.sample))
                policy, evidence = derive(db, scope, get_policy(db, scope), items, day)
                result = {"policy": put_policy(db, scope, policy), **evidence}
                if args.sample:
                    result["plan"] = plan(db, scope, args.sample)
            elif args.command in ("ask", "answer"):
                row, items = sample_data(db, scope, args.sample) if args.sample else (None, [])
                if args.command == "ask":
                    result = menu(args.network, items, args.lang, args.all)
                    result.update(scope=scope, sample=args.sample)
                    if row:
                        result.update(sample_context(db, scope, row))
                else:
                    choices = apply_answers(get_policy(db, scope), menu(args.network, items, expanded=True),
                                            args.reduce, args.encourage, args.keep, args.protect, args.replace)
                    for flag in ("boost_sources", "repair_youtube_history"):
                        if getattr(args, flag) is not None:
                            choices[flag] = getattr(args, flag)
                    result = put_policy(db, scope, choices)
            elif args.command == "plan":
                result = plan(db, scope, args.sample, args.reset_request)
            elif args.command == "save-resource":
                result = save_resource(db, scope, args)
            elif args.command == "record":
                result = record(db, scope, args)
            else:
                result = report(db, scope)
        output(result)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, sqlite3.Error) as error:
        sys.exit(f"feedreset: {error}")
