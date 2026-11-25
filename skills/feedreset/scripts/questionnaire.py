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
            "question": ("Qual desses conteúdos continua te prendendo depois que você já quer parar? "
                         "Quando isso acontece, o que você gostaria de estar fazendo, aprendendo ou cultivando na sua vida?"
                         if lang == "pt" else
                         "Which of these keeps pulling you back after you want to stop? "
                         "What would you like to be doing, learning or cultivating in your life instead?"),
            "follow_up_if_unclear": (
                "O que você sente falta de fazer ou admira em alguém? Pense, por exemplo, em ter mais paciência "
                "em casa, voltar a correr, aprofundar sua fé ou aprender um ofício. Qual pequena ação mostraria progresso?"
                if lang == "pt" else
                "What do you miss doing, or admire in someone? Think of patience at home, running again, "
                "deepening your faith or learning a craft. What small action would count as progress?")}


def apply_answers(previous, questionnaire, reduce, encourage, keep, protect, replacements=()):
    by_code = {opt["code"]: opt["topic"] for group in ("observed","optional_reduce","optional_encourage")
               for opt in questionnaire[group]}
    policy = dict(previous or {})
    def resolve(value):
        code = value.strip().upper()
        if code[:1] in ("O","E","R") and code[1:].isdigit() and code not in by_code:
            raise ValueError(f"Unknown option {value}")
        topic = canonical(by_code.get(code, value))
        if not topic:
            raise ValueError("Empty topic")
        return topic

    pairs = {(r["reduce"],r["cultivate"]): r for r in policy.get("replacements", [])}
    fields = {"reduce": list(reduce), "encourage": list(encourage), "keep_topics": keep}
    for trap, goal, practice in replacements:
        trap, goal = resolve(trap), resolve(goal)
        fields["reduce"].append(trap)
        fields["encourage"].append(goal)
        pairs[trap,goal] = {"reduce": trap, "cultivate": goal, "practice": practice}
    selected = {}
    for field, values in fields.items():
        for value in values:
            topic = resolve(value)
            if topic in selected and selected[topic] != field:
                raise ValueError(f"Conflicting choices for {topic}")
            selected[topic] = field
    if not selected and not protect:
        raise ValueError("Supply at least one choice or protected creator")
    for field in fields:
        current = {canonical(t) for t in policy.get(field, [])}
        policy[field] = sorted((current - selected.keys()) | {t for t, f in selected.items() if f == field})
    policy["protect"] = sorted(set(policy.get("protect", [])) | set(protect))
    policy["replacements"] = [r for (trap,goal),r in pairs.items()
                              if trap in policy["reduce"] and goal in policy["encourage"]]
    return policy
