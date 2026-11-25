"""Build the owner's choice menu from observed posts and optional prompts."""
from collections import Counter
import json
from pathlib import Path
import unicodedata


CATALOG = json.loads((Path(__file__).resolve().parents[1]/"references/topics.json").read_text(encoding="utf-8"))
TOPICS = {row[0]: row for row in CATALOG["topics"]}


def key(text):
    return unicodedata.normalize("NFKC", text.strip()).casefold()


ALIASES = {key(alias): row[0] for row in TOPICS.values() for alias in [row[0], row[2], row[3], *row[4]]}


def canonical(text):
    return ALIASES.get(key(text), key(text))


def menu(network, items, lang="pt", expanded=False):
    evidence = {}
    for item in items:
        for topic in sorted({canonical(t) for t in item["topics"]}):
            evidence.setdefault(topic, []).append(item)
    def option(code, topic):
        row = TOPICS.get(topic)
        label = row[2 if lang == "pt" else 3] if row else topic
        return {"code": code, "topic": topic, "label": label}

    observed = []
    for i, (topic, posts) in enumerate(sorted(evidence.items(), key=lambda pair: (-len(pair[1]), pair[0])), 1):
        votes = Counter(post["suggest"] for post in posts)
        suggestions = votes.most_common()
        suggestion = suggestions[0][0] if len(suggestions) == 1 or suggestions[0][1] > suggestions[1][1] else "uncertain"
        observed.append({**option(f"O{i}", topic), "observed_count": len(posts), "suggest": suggestion,
                         "examples": [{"id": p["id"], "label": p["label"], "reason": p["reason"]} for p in posts[:2]]})
    ordered = list(dict.fromkeys([*CATALOG["first"][network], *TOPICS]))
    extra = {"reduce": [], "encourage": []}
    for topic in ordered:
        if topic in evidence:
            continue
        group = TOPICS[topic][1]
        prefix = "R" if group == "reduce" else "E"
        extra[group].append(option(f"{prefix}{len(extra[group])+1}", topic))
    return {"sample_size": len(items),
            "observed": observed if expanded else observed[:6],
            "optional_reduce": extra["reduce"] if expanded else extra["reduce"][:5],
            "optional_encourage": extra["encourage"] if expanded else extra["encourage"][:3],
            "other_observed_count": 0 if expanded else max(0,len(observed)-6),
            "question": ("O que quer reduzir ao máximo, incentivar ou sempre preservar? "
                         "Responda com os códigos ou suas próprias palavras. Pode acrescentar qualquer assunto."
                         if lang == "pt" else
                         "What should I reduce strongly, encourage, or always keep? "
                         "Reply with codes or in your own words. Add any topic you like.")}


def apply_answers(previous, questionnaire, reduce, encourage, keep, protect):
    by_code = {opt["code"]: opt["topic"] for group in ("observed","optional_reduce","optional_encourage")
               for opt in questionnaire[group]}
    policy = dict(previous or {})
    fields = {"reduce": reduce, "encourage": encourage, "keep_topics": keep}
    selected = {}
    for field, values in fields.items():
        for value in values:
            code = value.strip().upper()
            if code[:1] in ("O","E","R") and code[1:].isdigit() and code not in by_code:
                raise ValueError(f"Unknown option {value}")
            topic = canonical(by_code.get(code, value))
            if not topic:
                raise ValueError("Empty topic")
            if topic in selected and selected[topic] != field:
                raise ValueError(f"Conflicting choices for {topic}")
            selected[topic] = field
    if not selected and not protect:
        raise ValueError("Supply at least one choice or protected creator")
    for field in fields:
        current = {canonical(t) for t in policy.get(field, [])}
        policy[field] = sorted((current - selected.keys()) | {t for t, f in selected.items() if f == field})
    policy["protect"] = sorted(set(policy.get("protect", [])) | set(protect))
    return policy
