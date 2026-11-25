#!/usr/bin/env python3
"""Account-scoped local memory for a personal feed curator. Python 3.9+."""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from questionnaire import apply_answers, canonical, menu

NETWORKS = ("instagram", "youtube", "tiktok", "x")
KINDS = ("encourage", "reduce", "uncertain")
SURFACES = ("recommendations", "following", "history")
OUTCOMES = ("verified", "user_reported", "needs_device", "unavailable")
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


def normalize_item(value):
    require(isinstance(value, dict), "Each item must be an object")
    item = {k: string(value.get(k), k) for k in ("id", "label", "reason", "suggest")}
    require(item["suggest"] in KINDS, "Invalid suggest value")
    item["topics"] = tags(value.get("topics"), "topics")
    item["creator"] = string(value["creator"], "creator") if value.get("creator") else ""
    url = value.get("url", "")
    require(isinstance(url, str), "url must be text")
    if url:
        u = urlsplit(url)
        require(u.scheme == "https" and u.hostname and not u.username and not u.password,
                "Use a public HTTPS link without credentials")
    item["url"] = url
    return item


def get_policy(db, scope):
    row = db.execute("SELECT data FROM policies WHERE scope=?", (scope,)).fetchone()
    return json.loads(row["data"]) if row else None


def put_policy(db, scope, raw):
    require(isinstance(raw, dict), "Expected a policy object")
    keys = {"encourage", "reduce", "protect", "keep_topics", "repair_youtube_history", "boost_sources"}
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
    topics = {canonical(t) for t in item["topics"]}
    if topics.intersection(policy.get("keep_topics", [])):
        return "protect"
    positive = topics.intersection(canonical(t) for t in policy["encourage"])
    negative = topics.intersection(canonical(t) for t in policy["reduce"])
    if positive and not negative:
        return "encourage"
    if negative and not positive:
        return "reduce"
    return "uncertain"


def action_id(control, target):
    return hashlib.sha256(json.dumps([control, target]).encode()).hexdigest()[:24]


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
    pending = []
    for control, target, label in actions:
        aid = action_id(control, target)
        existing = db.execute("SELECT outcome FROM actions WHERE scope=? AND id=?", (scope, aid)).fetchone()
        if existing and existing["outcome"] in ("verified", "user_reported"):
            continue
        pending.append({"id": aid, "control": control, "target": target, "label": label,
                        "previous_outcome": existing["outcome"] if existing else None})
    return {"scope": scope, "sample": sample, "surface": row["surface"], "counts": counts,
            "reading_queue": reading, "pending": pending}


def record(db, scope, args):
    actions = plan(db, scope, args.sample, args.reset_request)["pending"]
    action = next((a for a in actions if a["id"] == args.action), None)
    existing = db.execute("SELECT evidence,outcome FROM actions WHERE scope=? AND id=?",
                          (scope, args.action)).fetchone()
    evidence = string(args.evidence, "evidence")
    if existing and tuple(existing) == (evidence, args.outcome):
        return {"id": args.action, "outcome": args.outcome}
    if action is None and existing and existing["outcome"] == "user_reported" and args.outcome == "verified":
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
    for name in ("audit", "policy"):
        commands.add_parser(name).add_argument("file", help="JSON path, or - for stdin")
    for name in ("ask", "answer"):
        sub = commands.add_parser(name)
        sub.add_argument("sample", nargs="?", help="Omit to use general prompts only")
        if name == "ask":
            sub.add_argument("--lang", choices=("pt","en"), default="pt")
            sub.add_argument("--all", action="store_true", help="Show every optional topic")
        else:
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
            elif args.command == "policy":
                result = put_policy(db, scope, read_json(args.file))
            elif args.command in ("ask", "answer"):
                row, items = sample_data(db, scope, args.sample) if args.sample else (None, [])
                if args.command == "ask":
                    result = menu(args.network, items, args.lang, args.all)
                    result.update(scope=scope, sample=args.sample)
                    if row:
                        result.update(sample_context(db, scope, row))
                else:
                    choices = apply_answers(get_policy(db, scope), menu(args.network, items, expanded=True),
                                            args.reduce, args.encourage, args.keep, args.protect)
                    for flag in ("boost_sources", "repair_youtube_history"):
                        if getattr(args, flag) is not None:
                            choices[flag] = getattr(args, flag)
                    result = put_policy(db, scope, choices)
            elif args.command == "plan":
                result = plan(db, scope, args.sample, args.reset_request)
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
