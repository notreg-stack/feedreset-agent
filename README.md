# FeedReset

**Give your AI a job: reclaim your feed.** FeedReset is an open agent skill for Instagram, YouTube, TikTok and X. Your assistant examines the recommendations you actually receive, shows what appears useful or distracting, asks what *you* want more or less of, and uses those choices for daily maintenance. A stray click doesn't get a vote.

[Guia em português](README.pt-BR.md) · [Download the skill](https://github.com/notreg-stack/feedreset-agent/releases/latest) · [What each network allows](skills/feedreset/references/platforms.md)

## Try it with your AI

Give an agent with repository access this prompt:

> Open https://github.com/notreg-stack/feedreset-agent and follow skills/feedreset/SKILL.md. Start with my most-used feed. Show me concrete examples of what appears constructive, distracting or uncertain. Ask what I want to encourage, reduce and always keep. Then apply my choices as strongly as my account controls allow and set up a daily pass if your host can schedule it.

**Claude Code and Codex:** open a checkout and send the prompt. **Claude, Grok or another chat:** share the skill and its references folder, plus a few consecutive screenshots if the chat can't see the feed. On an iPhone, screenshots are enough for a first diagnosis. Account changes require a supported integration or native taps. A chat without a scheduler can give you a reusable policy card.

## A question grounded in your feed

First come patterns actually seen on your iPhone or desktop browser, with examples and counts. Then come optional prompts for that network: cliffhanger clips, outrage bait, transfer rumors, betting promotions, impulse-shopping videos or productivity tips that never demonstrate the technique. Choose what to cut, what to increase, what to always keep, and add anything in your own words. [How the interview works and what the research supports](skills/feedreset/references/interview.md)

## What a diagnosis looks like

This example is fictional. The assistant first sees five YouTube recommendations. The owner then says “more worked examples, cut transfer gossip, always keep my friend.”

| Evidence on screen | Decision after the owner's choices |
| --- | --- |
| A mechanic shows the whole repair, including the failed attempt | Keep both videos. Offer to prioritize the channel. |
| A third post repeats an anonymous transfer rumor | Apply the available negative-feedback control. |
| A friend posts about a new teammate | Keep the friend, even though the topic matches a reduction. |
| A teaser has too little visible evidence | Leave it undecided. |

Run the same example locally. Python 3.9+ is the only dependency.

```sh
git clone https://github.com/notreg-stack/feedreset-agent.git
cd feedreset-agent
python3 demo.py
```

## What happens tomorrow

The agent opens each available account, samples the same surface, applies standing choices, and returns a short receipt: how much unwanted material it actually saw, which changes it verified, what still needs a tap, and one useful thing to open. It can remove a specific unwanted YouTube watch-history signal with permission. Instagram and TikTok have broader reset controls for an explicitly chosen fresh start. Repeated full resets would also discard useful learning.

**Daily on a Mac or Linux computer:** complete one interactive diagnosis and save your choices. Use a scheduler on a host that has access to the account. For example, open `crontab -e` and add one line with the real absolute paths on that machine. The example runs at 08:00 host time. Use your Python 3.9+ executable and a writable private directory for the log.

```cron
0 8 * * * /absolute/path/to/python3 /absolute/path/to/feedreset-agent/skills/feedreset/scripts/daily.py codex --binary /absolute/path/to/codex >> "$HOME/.feedreset/daily.log" 2>&1
```

Use `claude --binary /absolute/path/to/claude` in place of the Codex arguments for Claude Code. Check the installed job with `crontab -l` and the first run's log. A sleeping host, a locked device or a host without suitable permissions can leave work pending. The launcher uses the CLI's existing permissions and prevents overlapping scheduled passes. Use `python3 skills/feedreset/scripts/daily.py prompt` to print the enrolled-account prompt for another capable scheduler. On iPhone, use a host integration or Shortcut that actually exposes the required action. [iPhone workflow and platform controls](skills/feedreset/references/platforms.md)

## What stays private

The local helper stores account aliases, compact evidence, choices and receipts in `~/.feedreset/state.sqlite3`. It uses the Python standard library and makes no network requests. The AI you choose may process screenshots or data you share according to that provider's settings. Use fictional evidence in public issues. [Local data format and commands](skills/feedreset/references/memory.md)

The agent instructions work without Python. Automatic access, writes and scheduling depend on the host and platform. The repository ships the protocol, local tools and a verified offline demo. Live results vary by account, region and available controls.
