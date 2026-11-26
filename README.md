# FeedReset

**Cut the distractions that keep coming back. Put work worth learning from in their place.** Give your AI access to the feeds you use. It diagnoses Instagram, YouTube, TikTok and X together, builds a substantial reconstruction plan from the available history, and maintains it daily. Its editorial target is **95% reorientation of the sampled feed mix toward substantive content**.

[Português](README.pt-BR.md) · [Download the agent](https://github.com/notreg-stack/feedreset-agent/releases/latest) · [How 95% is measured](skills/feedreset/references/intentional.md)

Approve examples once. FeedReset uses them to select replacements and scores the first 20 organic recommendations after a round of changes. The report also identifies recurring YouTube channels by channel ID and keeps receipts for native feedback. [Example-driven curation and commands](skills/feedreset/references/feedback.md)

## Give this to your AI

> Open https://github.com/notreg-stack/feedreset-agent and follow skills/feedreset/SKILL.md. Audit all my available feeds and history. Cut memes, viral entertainment, repetitive comedy, politics and football. Find the virtuous practice, real economic work and technical depth I've already engaged with. Rebuild around stronger sources, preserve my exceptions and maintain the result daily. Act on the evidence and ask only when my answer would materially change a decision.

For Codex or Claude Code, open a checkout. For a chat such as Grok or Claude, share the skill and its references. Supported account tools can read and act; iPhone screenshots can establish what appeared on screen. Daily access and writes depend on the host's integrations.

## What the first pass delivers

| Stage | What the agent does |
| --- | --- |
| Diagnose all accounts | Samples actual recommendations and reads watch/open history separately. Marks missing access and keeps going. |
| Build the plan | Identifies recurring unwanted patterns and hunts for constructive history: an operator's first-hand case, a demonstrated technical fix, or a practice the owner values. |
| Rebuild | Offers an eligible broad reset, uses permitted native feedback and chooses replacement sources. Shows what changed, what was verified and which native tap is pending. |
| Maintain | Revisits each available account daily, catches returning distractions and makes better clicks easy through selected sources, subscriptions or a private list. |
| Measure | Compares the same feed before and after, reports evidenced user-open behavior separately and preserves the owner's corrections. A missing account keeps the overall result pending. |

A fictional example: yesterday's history contains sports rumors and a workshop operator debugging defective parts. The agent cuts the recurring rumors, looks for more first-hand production engineering and gives the owner a specific case to open next. A play recorded by autoplay carries no evidence of a chosen click.

Try the four-account offline demo with Python 3.9+:

```sh
git clone https://github.com/notreg-stack/feedreset-agent.git
cd feedreset-agent
python3 demo.py
```

## What happens tomorrow

The agent opens each available account, samples the same surface, applies standing choices, and returns a short receipt: how much unwanted material it actually saw, which changes it verified, what still needs a tap, and one useful thing to open. It can remove a specific unwanted YouTube watch-history signal with permission. Instagram and TikTok have broader reset controls for an explicitly chosen fresh start. Repeated full resets would also discard useful learning.

**Daily on a Mac or Linux computer:** run the initial audits and apply the intentional curation profile. Use a scheduler on a host that has access to the account. For example, open `crontab -e` and add one line with the real absolute paths on that machine. The example runs at 08:00 host time. Use your Python 3.9+ executable and a writable private directory for the log.

```cron
0 8 * * * /absolute/path/to/python3 /absolute/path/to/feedreset-agent/skills/feedreset/scripts/daily.py codex --binary /absolute/path/to/codex >> "$HOME/.feedreset/daily.log" 2>&1
```

Use `claude --binary /absolute/path/to/claude` in place of the Codex arguments for Claude Code. Check the installed job with `crontab -l` and the first run's log. A sleeping host, a locked device or a host without suitable permissions can leave work pending. The launcher uses the CLI's existing permissions and prevents overlapping scheduled passes. Use `python3 skills/feedreset/scripts/daily.py prompt` to print the enrolled-account prompt for another capable scheduler. On iPhone, use a host integration or Shortcut that actually exposes the required action. [iPhone workflow and platform controls](skills/feedreset/references/platforms.md)

## What stays private

The local helper stores account aliases, compact evidence, choices and receipts in `~/.feedreset/state.sqlite3`. It uses the Python standard library and makes no network requests. The AI you choose may process screenshots or data you share according to that provider's settings. Use fictional evidence in public issues. [Local data format and commands](skills/feedreset/references/memory.md)

The agent instructions work without Python. Automatic access, writes and scheduling depend on the host and platform. The repository ships the protocol, local tools and a verified offline demo. Live results vary by account, region and available controls.
