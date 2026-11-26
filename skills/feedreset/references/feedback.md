# From approved examples to ordinary recommendations

An example earns its place by what someone can learn from it. For a fictional robotics post, “a technician measures drift before and after recalibration” is a more useful reference than “a robot went viral.” A second creator can demonstrate the same skill on different equipment. Preserve that reason and the stable editorial focus when auditing both videos.

## Record the owner's selection

From the skill directory, use the same network and account alias throughout. A discovery JSON uses the ordinary audit format with `surface` set to `discovery`. Each item needs an ID, label, stable focus, topics, reason, substantive merit and an `encourage` suggestion. Include its public URL when available. The identifiers below are fictional.

```sh
python3 scripts/feedreset.py --network youtube --account personal audit discovery.json
python3 scripts/feedreset.py --network youtube --account personal approve workshop-picks --items demo-jig demo-bearing
python3 scripts/feedreset.py --network youtube --account personal curate after-feedback
```

Use `approve workshop-picks --all` when the owner selected the entire audited set. Use `unapprove demo-jig` to remove a reference. These operations write to the local database. Replaying a selection keeps one reference per item and account. A correction to the owner's reduction policy takes precedence. In `rebuild_proposal.source_priorities`, approved subjects with the most examples get first consideration and each carries a concrete example to find more work like it. The owner can approve additional examples in underrepresented subjects.

## Measure the next scroll

1. Finish applying the controls for this round. Open the ordinary recommendation surface on the enrolled account. Record the device and feed name.
2. Capture consecutive recommendations in order. Keep a separate count of sponsored placements. Include unreadable or ambiguous organic posts with `merit: unknown`. Audit this batch with its own sample ID. If another cut happens mid-measurement, keep the interrupted batch as a separate observation and start a new measurement.
3. Read `plan.reference_score` from `curate`, or `reference_score` from `plan`. It uses the first 20 organic entries in that sample, or all available entries for a partial sample. A match requires an approved main focus and a substantive `encourage` assessment based on observable evidence, subject to the current policy. The agent makes the evidence assessment. The helper applies an explicit rule to it. Exact approved IDs that reappear are listed separately. With no approved examples the percentage is unavailable.
4. Nineteen matches in twenty gives 95% for that sample. The gap field reports how many additional aligned slots that sample would need. For overall reorientation, compare a later day's feed to the frozen baseline with `progress.py`. Each item moves a twenty-item estimate by five percentage points. Repeated observations on different days give a better basis for a claim about persistence.

## Escalate a recurring source

Prefer item feedback for an isolated distraction. For YouTube, attach the canonical channel ID to an audited item as `source_id` when the host can establish it. Keep the human-readable creator in `creator`. With the ID absent, item-level curation still works.

`plan.channel_evidence` lists distinct low-value item IDs and their reasons from the same account, device and feed in the preceding 30 days through the current sample. Two distinct eligible items from a channel, including one in today's sample, can produce a `dont_recommend_channel` proposal. A useful, protected or uncertain observation carrying the same source ID in that account's recent audits rules it out. An approved example bearing that source ID also rules it out while approved. Review the source and the owner's standing choices before acting.

Record a platform acknowledgement as `verified`. If the menu merely closes, use `record SAMPLE ACTION_ID submitted_unconfirmed "Menu closed after selecting Not interested"`. The action appears under `awaiting_readback` for that sample. A later readback can upgrade its receipt. A subsequent recommendation sample can surface a reversible item again. An unconfirmed whole-account reset stays pending verification across samples.

## Research behind these decisions

- BlockTube identifies individual videos and channels separately. FeedReset borrows that distinction for native feedback proposals. Browser-side hiding has a different effect from changing an account's recommendations. [BlockTube](https://github.com/amitbl/blocktube)
- DeArrow lets contributors replace sensational titles with accurate descriptions. FeedReset uses a neutral description of the actual demonstration when judging an item. A popular clip can still be a strong example. [DeArrow](https://github.com/ajayyy/DeArrow)
- FreeTube organizes subscriptions into profiles and stores them locally. FeedReset uses a private reference set per account so the owner can carry a chosen editorial direction into an audit of the native feed. [FreeTube](https://github.com/FreeTubeApp/FreeTube)
- Mozilla's 2022 RegretsReporter study observed recommendations after user feedback and found that unwanted content could recur. Its results motivate a follow-up sample. They do not predict an individual account's response today. [Original study](https://www.mozillafoundation.org/en/youtube/user-controls/)

Native controls depend on the surface and account. Check what the platform shows at the moment of action. [YouTube recommendation controls](https://support.google.com/youtube/answer/6342839?hl=en) · [Instagram recommendation controls](https://about.fb.com/news/2024/11/introducing-recommendations-reset-instagram/)
