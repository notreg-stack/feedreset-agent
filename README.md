# FeedReset

**Cut the content you keep getting pulled back into. Make room for what you want to cultivate in your life.** FeedReset gives your AI an interview and tools to do both. It inspects your Instagram, YouTube, TikTok or X feed, asks what unwanted habits crowd out, and finds sources that help you act on your answer. A goal can be missing from every post in your feed.

[Guia em português](README.pt-BR.md) · [Download the skill](https://github.com/notreg-stack/feedreset-agent/releases/latest) · [What each network allows](skills/feedreset/references/platforms.md)

## Try it with your AI

Give an agent with repository access this prompt:

> Open https://github.com/notreg-stack/feedreset-agent and follow skills/feedreset/SKILL.md. Find what keeps pulling me back against my intentions. Ask me questions to discover what I want to cultivate instead, even if it never appears in my feed. Find content I can act on, apply my choices where my account permits and maintain them daily.

**Claude Code and Codex:** open a checkout and send the prompt. **Claude, Grok or another chat:** share the skill and its references folder, plus a few consecutive screenshots if the chat can't see the feed. On an iPhone, screenshots are enough for a first diagnosis. Account changes require a supported integration or native taps. A chat without a scheduler can give you a reusable policy card.

## From an unwanted habit to something worth doing

In the demo, transfer rumors keep turning up on YouTube. The agent asks what those evenings crowd out. The viewer misses spending time with his daughter but hasn't chosen an activity. “Would you rather talk together or make something together?” leads to a specific answer: “She wants to cook with me. Let's make breakfast on Saturday.”

That answer changes the curation. The agent reduces the rumor videos, preserves the friend's channel and searches outside the existing feed for a recipe the two can make together. The offline demo includes a real pancake recipe with simple measuring and mixing tasks. The next conversation can start with “Did you make breakfast together?” [Recipe used in the demo](https://www.jamieoliver.com/recipes/healthy-breakfast-ideas/buddys-one-cup-pancakes/) · [Interview and evidence guide](skills/feedreset/references/interview.md)

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
