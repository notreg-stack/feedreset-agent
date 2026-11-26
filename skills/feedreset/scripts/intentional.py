"""Build an editorial policy from observed content without equating a view with a preference."""
import json
from collections import defaultdict
from datetime import date, timedelta

from questionnaire import canonical

MERITS = ("applied-practice", "economic-work", "technical-depth", "primary-evidence", "chosen-virtue")
DEFAULT_REDUCE = (
    "memes", "viral-entertainment", "general-humor", "all-politics", "all-football",
    "sports-rumors", "endless-clips", "ragebait", "betting-promos", "quick-money",
    "empty-tutorials", "celebrity-gossip", "impulse-shopping",
)
DEFAULT_ENCOURAGE = ("worked-examples", "economic-cases", "technical-demonstrations", "firsthand-evidence")


def quality_evidence(item):
    return item.get("merit") in MERITS and item["suggest"] == "encourage" and bool(item.get("focus"))


def derive(db, scope, current, feed_items, day):
    policy = dict(current) if current is not None else {"boost_sources": True}
    assigned = {canonical(t) for field in ("encourage", "reduce", "keep_topics") for t in policy.get(field, [])}
    history = defaultdict(dict)
    opened_traps = defaultdict(set)
    since = (date.fromisoformat(day) - timedelta(days=30)).isoformat()
    rows = db.execute("SELECT data FROM samples WHERE scope=? AND surface='history' AND day BETWEEN ? AND ? ORDER BY day DESC,rowid DESC",
                      (scope, since, day))
    for row in rows:
        for item in json.loads(row["data"]):
            if item.get("entry") == "user-opened" and item.get("focus") and item["suggest"] == "reduce":
                opened_traps[canonical(item["focus"])].add(item["id"])
            if quality_evidence(item) and item.get("entry") != "autoplay":
                focus = canonical(item["focus"])
                history[focus].setdefault(item["id"], item["reason"])
    recurring = defaultdict(set)
    for item in feed_items:
        if item["suggest"] == "reduce" and item.get("focus"):
            recurring[canonical(item["focus"])].add(item["id"])
    examples = list(db.execute("SELECT item,focus,label,reason,url FROM approved_examples WHERE scope=? ORDER BY item",
                               (scope,)))
    approved_subjects = {r["focus"] for r in examples}
    reduce = set(DEFAULT_REDUCE) | {focus for focus, ids in recurring.items()
                                    if len(ids) >= 2 and focus not in approved_subjects}
    encourage = set(DEFAULT_ENCOURAGE) | set(history)
    conflicts = reduce & encourage
    for field, candidates in (("reduce", reduce), ("encourage", encourage)):
        policy[field] = sorted(set(policy.get(field, [])) | (candidates - assigned - conflicts))
    ranked = sorted(history, key=lambda t: (-len(history[t]), t))
    references = defaultdict(list)
    for example in examples:
        if example["focus"] not in policy["reduce"]:
            references[example["focus"]].append(dict(example))
    approved_focuses = sorted(references, key=lambda focus: (-len(references[focus]), focus))
    goals = [t for t in dict.fromkeys(ranked + list(DEFAULT_ENCOURAGE)) if t in policy["encourage"]]
    replacements = list(policy.get("replacements", []))
    owner_traps = {r["reduce"] for r in replacements if r.get("origin", "owner") == "owner"}
    actionable = [t for t in recurring if t in policy["reduce"] and t not in owner_traps]
    actionable.sort(key=lambda t: (-len(opened_traps[t]), -len(recurring[t]), t))
    if goals:
        replacements = [r for r in replacements if r["reduce"] not in actionable]
        for index, trap in enumerate(actionable):
            goal = goals[index % len(goals)]
            replacements.append({"reduce": trap, "cultivate": goal,
                                 "practice": "Use a concrete example of " + goal,
                                 "origin": "history" if goal in history else "editorial"})
    policy["replacements"] = replacements
    # Allocate a proposed mix of organic slots. This is a sourcing brief, never an observed result.
    target_slots = (95 * len(feed_items) + 99) // 100
    other_priorities = [t for t in [*ranked, *DEFAULT_ENCOURAGE, *policy["encourage"]] if t in policy["encourage"]]
    priorities = list(dict.fromkeys([*approved_focuses, *other_priorities]))[:3]
    sourcing = []
    if priorities and target_slots:
        each, extra = divmod(target_slots, len(priorities))
        for i, goal in enumerate(priorities):
            slots = each + int(i < extra)
            if slots:
                direction = {"focus": goal, "proposed_slots": slots, "basis": "history" if goal in history else "policy"}
                if goal in references:
                    direction.update(basis="approved_examples", example=references[goal][0])
                sourcing.append(direction)
    return policy, {
        "rebuild_proposal": {"target_pct": 95, "baseline_or_current_slots": len(feed_items),
                             "minimum_target_slots": target_slots, "source_priorities": sourcing},
        "history_directions": [{"focus": k, "distinct_items": len(v), "examples": list(v.values())[:2]}
                               for k,v in sorted(history.items(), key=lambda pair: (-len(pair[1]), pair[0]))],
        "recurring_low_value": {k: len(ids) for k, ids in recurring.items() if len(ids) >= 2},
        "user_opened_unwanted": {k: len(ids) for k, ids in opened_traps.items() if ids and k in policy["reduce"]},
        "mixed_evidence": sorted(conflicts),
    }
