# Intentional curation and measurement

## Audit and act

Keep four separate rows in the diagnosis: Instagram, YouTube, TikTok and X. Each row names its access level, feed sample, history sample, principal unwanted patterns, positive evidence, planned changes and verified results. Use the same local alias only for accounts confirmed to belong to the owner.

For each audited item, supply a stable `focus` (one broad editorial subject), a `merit`, and a short observable reason. Reuse the same taxonomy across dates, languages and devices. A new creator, phrasing or post ID is insufficient reason to relabel a subject. Use the same focus for weak and strong posts about a subject; the merit captures the difference. Allowed merits are `low-value`, `unknown`, `applied-practice`, `economic-work`, `technical-depth`, `primary-evidence` and `chosen-virtue`. Add narrower action tags where relevant. Use `chosen-virtue` when the person's goals or observable practice support it. For watch history, add `entry: user-opened` only when the source establishes a user open. Otherwise use `autoplay` or `unknown`. A standard Takeout watch entry alone establishes a view.

Example of a fictional history item:

```json
{"id":"demo-01","label":"A workshop traces a defect to a worn jig","focus":"production engineering","topics":["technical-demonstrations"],"merit":"technical-depth","reason":"The operator measures the error, replaces the jig and repeats the measurement.","suggest":"encourage","entry":"unknown"}
```

Audit recommendation and history samples separately. Use the actual device and a named feed, e.g. `desktop` and `Home`. Run these commands from the skill directory, substituting real aliases and sample IDs:

```sh
python3 scripts/feedreset.py --network youtube --account personal audit history.json
python3 scripts/feedreset.py --network youtube --account personal audit home.json
python3 scripts/feedreset.py --network youtube --account personal curate initial-home
python3 scripts/feedreset.py --network youtube --account personal plan initial-home
python3 scripts/progress.py --scope instagram/personal --scope youtube/personal --scope tiktok/personal --scope x/personal
```

`curate` anchors the first recommendation sample, reads the preceding 30 days of audited history for this account, applies the cut list and ranks distinct substantive history items. It keeps explicit corrections and protected creators. Its reconstruction brief allocates at least 95% of the reference sample size to stronger source directions. These are proposed slots, not earned measurement credit. It returns recurring low-value subjects and evidenced opens of unwanted topics. It pairs observed cuts with directions from history or editorial starting points. A replacement with origin `history` or `editorial` is an agent decision and can be corrected at any time. A user-authored replacement takes precedence. Running `curate` without a sample can initialize an available account from history and defaults while access to recommendations is pending. Each command is local; native changes need the host's supported executor and a receipt.

Prioritize actionable alternatives. For example, replace business-motivation clips with a plant manager's before-and-after defect analysis, or a founder's demonstration of the actual customer acquisition process. Apply eligible source controls as part of the same pass. Track repeated unwanted openings privately and adjust the default viewing route. When the owner offers a correction use `answer --reduce`, `--encourage`, `--keep`, `--protect` or `--replace`. A correction is sufficient; no new onboarding interview is needed.

## What counts toward 95%

The target is a substantial change in **the whole observed recommendation mix** toward high-value content. A feed that was already excellent can score highly for quality while showing little change. Honor the owner's good sources even when this keeps the change metric below target.

1. Compare the frozen baseline with distinct organic items on a later day from the same account, device and named feed. Include unknowns in the denominator; keep them out of the high-value numerator. Use at least 20 before and 20 after for a measured result. Smaller samples are provisional; proceed with curation at any size.
2. Group substantively high-value baseline items by stable editorial focus. For each focus, calculate how much its share of **aligned, high-value content today** exceeds its original substantive share. Sum the positive differences. Deduct the baseline share with insufficient evidence; cap the result at the share of aligned high-value items with IDs absent from the baseline. This conservative estimate measures shifts into substantive subjects or higher-quality treatment and resists mere post-ID turnover. Use consistent labeling; rerating old subjects can distort the estimate.
3. Weight accounts by their fixed baseline sample sizes. Keep the combined value pending if any requested account lacks a comparable measurement. Mark whether the named scopes cover all four networks. A 95% result describes the sampled feeds. Compare with yesterday when both samples qualify. Report percentage-point changes and unwanted topics whose shares grew, including when all the post IDs changed.
4. Report current high-value share alongside reorientation. For behavior, report the count and share of high-quality, demonstrably user-opened items on the baseline and comparison dates. Autoplay and unknown provenance are excluded from this behavioral denominator. A movement in these samples does not establish the cause of a change in habits.

For example, with 20 low-value baseline items and 19 distinct high-value replacements in 20 later recommendations, the sample can reach 95%. If all 20 were already high-quality treatments of the same subject and only their IDs change, reorientation is zero. Verified account actions, resources discovered by search and Following feeds contribute no points to this measure.
