#!/usr/bin/env python3
"""Compare observed recommendation mixes and evidenced user-opened items across accounts."""
import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

from feedreset import NETWORKS, decision, get_policy, norm, require, sample_context, sample_data
from intentional import quality_evidence
from questionnaire import canonical

TARGET = Fraction(95, 100)
MIN_SAMPLE = 20


def percent(share):
    return round(float(share * 100), 2)


def aligned(item, policy):
    return quality_evidence(item) and decision(item, policy) in ("encourage", "protect")


def exposure_change(before, after, policy):
    old = Counter(canonical(i["focus"]) for i in before if quality_evidence(i))
    unknown = sum(i.get("merit", "unknown") == "unknown" or
                  (i.get("merit") != "low-value" and not quality_evidence(i)) for i in before)
    new = Counter(canonical(i["focus"]) for i in after if aligned(i, policy))
    gain = sum(max(Fraction(), Fraction(n, len(after)) - Fraction(old[t], len(before))) for t,n in new.items())
    gain = max(Fraction(), gain - Fraction(unknown, len(before)))
    original_ids = {i["id"] for i in before}
    fresh_quality = sum(aligned(i, policy) and i["id"] not in original_ids for i in after)
    return min(gain, Fraction(fresh_quality, len(after))), Fraction(sum(new.values()), len(after))


def items_on(db, scope, surface, day, context=None):
    rows = db.execute("SELECT * FROM samples WHERE scope=? AND surface=? AND day=? ORDER BY rowid",
                      (scope, surface, day))
    unique = {}
    for row in rows:
        if context is not None and sample_context(db, scope, row) != context:
            continue
        for item in json.loads(row["data"]):
            unique.setdefault(item["id"], item)
    return list(unique.values())


def opened(db, scope, day, policy):
    items = items_on(db, scope, "history", day)
    eligible = [i for i in items if i.get("entry") == "user-opened"]
    good = sum(aligned(i, policy) for i in eligible)
    unwanted = sum(decision(i, policy) == "reduce" for i in eligible)
    return {"user_opened": len(eligible), "aligned": good, "unwanted": unwanted,
            "other_or_unknown_entry": len(items)-len(eligible),
            "aligned_pct": percent(Fraction(good, len(eligible))) if eligible else None}


def progress(db, scopes, day):
    require(scopes and len(set(scopes)) == len(scopes), "Supply distinct network/account scopes")
    require(date.fromisoformat(day).isoformat() == day and day <= date.today().isoformat(), "Invalid observation day")
    results, weighted_change, weight = [], Fraction(), 0
    for scope in scopes:
        net, sep, account = scope.partition("/")
        require(net in NETWORKS and sep and account.strip(), "Use network/account for each scope")
        policy = get_policy(db, scope)
        result = {"scope": scope, "status": "missing_baseline"}
        results.append(result)
        anchor = db.execute("SELECT sample FROM baselines WHERE scope=?", (scope,)).fetchone()
        if not anchor or policy is None:
            continue
        row, before = sample_data(db, scope, anchor["sample"])
        context = sample_context(db, scope, row)
        result.update(context, baseline_day=row["day"], baseline_n=len(before),
                      opened_baseline=opened(db, scope, row["day"], policy),
                      opened_on_day=opened(db, scope, day, policy))
        if day <= row["day"]:
            result["status"] = "awaiting_later_day"
            continue
        after = items_on(db, scope, "recommendations", day, context)
        result["current_n"] = len(after)
        if not after:
            result["status"] = "missing_comparable_sample"
            continue
        gain, quality = exposure_change(before, after, policy)
        result.update(reoriented_pct=percent(gain), current_high_value_pct=percent(quality))
        if min(len(before), len(after)) < MIN_SAMPLE:
            result["status"] = "provisional_small_sample"
            continue
        result["status"] = "measured"
        yesterday = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
        previous = before if yesterday == row["day"] else items_on(db, scope, "recommendations", yesterday, context)
        result["change_since_yesterday_pp"] = None
        if len(previous) >= MIN_SAMPLE:
            previous_gain, _ = exposure_change(before, previous, policy)
            result["change_since_yesterday_pp"] = percent(gain - previous_gain)
            old_cuts = Counter(canonical(i["focus"]) for i in previous if i.get("focus") and decision(i, policy) == "reduce")
            new_cuts = Counter(canonical(i["focus"]) for i in after if i.get("focus") and decision(i, policy) == "reduce")
            result["unwanted_topics_growing_pp"] = {
                t: percent(Fraction(n, len(after)) - Fraction(old_cuts[t], len(previous))) for t, n in new_cuts.items()
                if Fraction(n, len(after)) > Fraction(old_cuts[t], len(previous))}
        weighted_change += gain * len(before)
        weight += len(before)
    complete = all(r["status"] == "measured" for r in results)
    total = weighted_change / weight if complete else None
    all_four = {s.split("/",1)[0] for s in scopes} == set(NETWORKS)
    return {"day": day, "target_pct": 95, "accounts": results, "covers_all_four_networks": all_four,
            "reoriented_pct_for_requested_scopes": percent(total) if complete else None,
            "sample_target_met_for_requested_scopes": total >= TARGET if complete else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path.home()/".feedreset"/"state.sqlite3")
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--scope", action="append", help="Repeat for each expected network/account, including unavailable accounts")
    args = parser.parse_args()
    scopes = [norm(s) for s in args.scope] if args.scope else [net+"/personal" for net in NETWORKS]
    if not args.db.is_file():
        sys.exit("No local observations. Run the initial audit and curate first.")
    db = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        # An existing v0.2 database gains its baseline on the first curate invocation.
        if not db.execute("SELECT name FROM sqlite_master WHERE name='baselines'").fetchone():
            sys.exit("No comparison baseline yet. Run curate on the first organic sample.")
        db.execute("BEGIN")
        print(json.dumps(progress(db, scopes, args.day), ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, sqlite3.Error) as error:
        sys.exit(f"feedreset: {error}")
