# Optional questions when a decision needs the owner

First run the intentional curation pass on all available accounts. Use this guide for a correction, a consequential ambiguity or a person who wants a guided interview. For routine decisions, act on the history and the editorial policy. Start from what the person saw. Use the catalog to help them recognize patterns they may want to cut. A catalog entry describes a possible preference. Its presence in the catalog establishes neither exposure nor a harmful effect on an individual.

## Capture on the device they actually use

- **iPhone:** when the host has an authorized view of the device, inspect the chosen feed. Otherwise accept consecutive screenshots or a short recording. Ask for the network and surface only if unclear. Read the visible caption, source and format; record when sound or context is missing.
- **Desktop browser:** use a permitted connected session for the correct account and surface. Otherwise accept consecutive screenshots from the actual browser tab. On X use a permitted integration for automation or owner-provided evidence. A public search, a creator's profile and a Following timeline cannot establish what For You is showing.
- When both devices are supplied, label the device, date and surface of each sample. Ask which surface matters most if their patterns differ. Keep history separate from exposure. Never infer dwell time, repeated intentional views or compulsive use from a screenshot.

## Ask after inspecting the sample

1. In each observed item, attach narrow stable topics supported by the content. Use the catalog's topic IDs where they fit, including a broad parent such as `all-football` only when the content supports it. Preserve novel topics in the person's language. For a useful economics explainer, add `all-politics` only if it genuinely addresses politics. A keyword alone is insufficient. Separate the judgment about the specific item from the broader subject tag.
2. Run `ask SAMPLE --lang pt` or `--lang en`. In hosts without Python, apply the same approach using [the catalog](topics.json). Count each post once for each topic it supports. Overlapping topics mean counts can exceed the sample total. Use at most a handful of first-turn choices and let the person expand the menu.
3. Show **seen in your feed** first: offer the strongest recurring personalized options, one recognizable example per pattern, and a constructive alternative grounded in an observed post when possible. For singletons say “seen once.” If many items concern a pattern absent from the catalog, that pattern still goes first.
4. Then show **other options for this network**: three to five prompts the person can choose preventively. Label them as unobserved in this sample. If a topic is already observed, show it only in the observed section. Offer the broader catalog, a whole-subject cut, or extra topics in their own words. Suggestions about sports, politics, leisure or identity are never automatic exclusions.
5. Use the questions below to discover what to put in place of the unwanted pattern. Keep **reduce / cultivate / always keep / add my own** available as simple answer options. Let them respond by code, by copying labels or in a sentence. Show the sample name with the choices and resolve codes against that same sample before saving. If several networks are involved, present one consolidated conversation, keep codes grouped by network and ask only if the requested scope is ambiguous.
6. Record only what the person selected, plus existing choices they have retained. A new answer can move a topic between reduce, encourage and always keep. Record named people or channels separately. If they want to cut short-form clips but preserve a friend's work, acknowledge and save the exception. With no evidence, show general options and state that observation is pending.

### Discover what deserves the space

Begin with one real pattern and listen for what it displaces. Someone may keep watching online arguments even after deciding to stop. Ask “What tends to get squeezed out on those evenings?” If they already know what to put in its place, use their words and skip the extra questions.

When the answer is “something useful” or “I don't know,” ask what they miss doing, whom they admire and why, or what they want to be able to do a month from now. Pick the question that follows naturally from their answer. Offer two hypotheses grounded in what they tell you. Possible directions include presence with family, patience, courage, generosity, faith or reflection, physical training, intellectual depth and mastery of a craft. Leave room for an unlisted answer. Never infer a belief, virtue or personal shortcoming from a social feed.

For example, a person who says “I want to be there for my daughter” might mean building something together or listening more patiently. Ask which would change the coming week. If they choose cooking together, search for a beginner recipe with a task they can do side by side. If they choose listening, seek a demonstrated conversation exercise. Those answers lead to materially different sources even when the rejected feed pattern is identical.

Offer a short summary for correction, then apply it: **what to cut → what to cultivate → how it would show up outside the app**. If a person wants to use the freed time entirely offline, honor that answer. Keep their feed reductions and skip replacement media for that time.

## Why these prompts are offered

The platform documents below explain why an unwanted click, prolonged view or interaction can influence subsequent ranking. They do not publish a population prevalence ranking of “most addictive topics.” The catalog is an editorial starting set; the observed menu is ordered by this person's sample. Never infer a clinical condition or assign values to the person from network-level research.

- TikTok describes watch time, watching in full or skipping, and other user interactions in its recommendation system. That motivates distinguishing chosen practice from repeated cliffhanger clips. [TikTok recommendation signals](https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content)
- Meta describes multiple predictions, such as likelihood of sharing, and controls across Feed, Reels and Stories. Treat an original Story and a recommended Reel as distinct evidence. [Meta's ranking overview](https://about.fb.com/news/2023/06/how-ai-ranks-content-on-facebook-and-instagram/)
- YouTube describes watch history and satisfaction signals. Filling different samples for Home and watch history helps identify a viewed item the person wants to remove. [YouTube recommendations](https://support.google.com/youtube/answer/16089387?hl=en)
- X describes using interaction signals to personalize recommendations. Repeated partisan conflict can be a worthwhile opt-out even when the person chooses to preserve factual reporting. [X recommendations](https://help.x.com/en/rules-and-policies/recommendations)
- Randomized headline experiments found negative wording increased clicks in the news setting studied. Separately, research on social networks found that social feedback can reinforce later expressions of moral outrage. These findings motivate offering alarmist headlines and outrage bait as choices. [Headline experiments](https://doi.org/10.1038/s41562-023-01538-4) · [Social learning and outrage](https://pmc.ncbi.nlm.nih.gov/articles/PMC8363141/)
