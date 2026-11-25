# Local audit, choices and receipts

Run from the skill directory. Python 3.9+ and its standard library suffice. Each invocation uses the same private database at `~/.feedreset/state.sqlite3`. Pass `--db PATH` before the subcommand for a different store. A consistent network/account pair is essential. Full data exports and screenshots belong outside the checkout.

1. Convert what you actually observed into the sample shape below. Supply a stable native post ID or permalink. For a screenshot without one, use the same stable fingerprint of creator + title across samples. A vague title belongs in uncertain. Use a verified stable creator handle/ID when available; omit it otherwise. Split surfaces into separate samples. For consecutive sessions, label the sample with its surface, e.g. `home-2026-06-05-a` or `reels-2026-06-05-a`. Compare only matching feeds. Use the observed local date. Re-importing an identical sample is safe.
2. Run the diagnosis and show counts and examples. Before papering over conflicts with a single broad tag, use narrow topics meaningful to the owner, e.g. `transfer rumors` and `match analysis`.
3. After the owner answers, store the complete current policy for each account. Include previous choices that still apply. A protected creator overrides reductions in this version. A post matching both an encouraged and a reduced topic stays uncertain. A classification suggested during diagnosis never authorizes an action on its own.
4. Generate the plan, perform supported actions through the host and record an evidence-bearing outcome. A pending action is only a proposal. For an unavailable control, read the previous receipt and retry only when access or evidence changes. If the user already completed a tap, verify current state before trying again. Only an independent readback upgrades a user-reported tap to verified.
5. Report sample sizes and outcomes. Saved samples can be re-evaluated under a revised policy. The terminal output contains private interests; keep it local.

```sh
python3 scripts/feedreset.py --network youtube --account personal audit sample.json
python3 scripts/feedreset.py --network youtube --account personal ask home-2026-06-05-a --lang pt
# After the owner picks, use codes from that exact menu or custom topic strings.
python3 scripts/feedreset.py --network youtube --account personal answer home-2026-06-05-a --reduce O1 "celebrity gossip" --keep "local club matches" --encourage "creative practice" --boost-sources
# Alternatively, import the complete approved policy.
python3 scripts/feedreset.py --network youtube --account personal policy policy.json
python3 scripts/feedreset.py --network youtube --account personal plan home-2026-06-05-a
python3 scripts/feedreset.py --network youtube --account personal record home-2026-06-05-a ACTION_ID verified "Observed YouTube's feedback confirmation on the exact video"
python3 scripts/feedreset.py --network youtube --account personal report
```

Sample shape with a fictional item:

```json
{"sample":"home-2026-06-05-a","day":"2026-06-05","surface":"recommendations","device":"iphone","feed":"Home","items":[{"id":"fictional-001","label":"Why the transfer deal is always one day away","creator":"demo-rumors","topics":["transfer rumors"],"reason":"Teases an unnamed signing and supplies no source.","suggest":"reduce"}]}
```

Allowed surfaces are `recommendations`, `following` and `history`. Allowed diagnostic suggestions are `encourage`, `reduce` and `uncertain`. Use `device` (`iphone`, `desktop`, `other` or `unknown`) and `feed` (e.g. Home, Reels, For You) to preserve the capture context. The optional `url` is a public HTTPS permalink. Keep raw captions and viewer identifiers out of the ledger when a short label and reason suffice.

```json
{"encourage":["worked examples","match analysis"],"reduce":["transfer rumors"],"protect":["my-friend"],"boost_sources":true,"repair_youtube_history":true}
```

`boost_sources` permits prioritizing a source after two distinct encouraged items in the current sample and no mixed item from that source. Verify the appropriate native operation first. `repair_youtube_history` is specific to YouTube. Confirm the exact history entry and the already-granted standing permission before acting. A verified or user-reported item action drops out of future plans for that account. Supported receipt outcomes are `verified`, `user_reported`, `needs_device` and `unavailable`.

For a separately confirmed Instagram/TikTok reset, attach the same one-shot ID to both `plan SAMPLE --reset-request ID` and `record SAMPLE ACTION_ID OUTCOME EVIDENCE --reset-request ID`. Use an ID tied to the person's specific decision. Never mint a fresh ID to repeat a previous decision. After an interrupted reset, check live state and the last receipt first.

For a YouTube Takeout export, select YouTube watch history in JSON and unzip it privately. Extract local evidence with `python3 scripts/takeout.py /path/to/watch-history.json --limit 20`. The helper selects the latest distinct videos and retains their timestamps. Classify the resulting rows before audit and separate observation dates. If the owner supplies HTML, screenshots or a different export shape, describe the evidence you can read directly.

Use `ask --all` (or `ask SAMPLE --all`) to expand the optional catalog. Omitting the sample produces general suggestions only. The `answer` command merges selected topics into the existing policy. A topic selected with `--keep` is always preserved, including on an otherwise mixed post. Protected creators use `--protect`. When collecting input without a CLI, use [the interview guide](interview.md).
