# Tweet Variations Generator + Scheduler

A complete content system for X (Twitter):
- 🤖 Takes any idea (in English or Hebrew) → returns **5 English tweet variations** from different angles (Hook / Story / List / Question / Insight)
- 🎯 Interactive selection with a "regenerate" option
- 📊 **Automatic history** saved to CSV + per-style statistics
- 📅 **Automatic scheduling** via Typefully (optional)
- 🌐 You can write the idea in Hebrew — the tweets always come back in English

## Quick Start (3 steps)

```bash
# 1. Install
pip install anthropic

# 2. Required API key (from console.anthropic.com)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Optional — for auto-scheduling (from typefully.com/settings/integrations)
export TYPEFULLY_API_KEY="..."
```

Tip: add the `export` lines to `~/.zshrc` so they persist across sessions.

## Usage

### Generate variations
```bash
python tweet_variations.py "What I learned this year about building products"
```

You'll get 5 variations, then:
- **1–5** — pick a variation
- **r** — regenerate (5 fresh ones)
- **q** — quit without saving

After you pick one:
- **s** — save to history (default)
- **c** — print for quick copy + save
- **n** — schedule in Typefully at the next free slot *(if API key is set)*
- **d** — schedule for a specific date *(if API key is set)*



### View history and stats
```bash
python tweet_variations.py --history          # last 20
python tweet_variations.py --history --limit 50

python tweet_variations.py --stats            # breakdown by style + action
```

## Sample Output

```
────────────────────────────────────────────────────────────
#1  🪝 Hook  (187 chars)
────────────────────────────────────────────────────────────
Most "product advice" online is just survivorship bias dressed up
in confident language. The same founder who succeeded by
"following their gut" would've blamed it on the market if they'd failed.

────────────────────────────────────────────────────────────
#2  📖 Story  (243 chars)
────────────────────────────────────────────────────────────
Two years ago I launched 4 products in 12 months. Three failed...
```

## Files the system creates

- `history.csv` — full history (timestamp, idea, style, char_count, tweet, action, scheduled_for)
- No database — everything lives in a single CSV you can open in Excel/Numbers

## Architecture — how it works

1. **Model:** `claude-opus-4-7` with streaming (avoids HTTP timeouts)
2. **Structured outputs:** a JSON schema guarantees you always get exactly 5 variations in valid format — no broken parsing
3. **System prompt:** steers the model toward five specific angles, limits length, and avoids unnecessary hashtags/emojis
4. **Typefully API:** simple REST call (uses `urllib`, zero extra dependencies); supports `next-free-slot` or ISO 8601

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY not set` | `export ANTHROPIC_API_KEY="sk-ant-..."` |
| Variation over 280 chars | A ⚠️ warning appears — edit manually, or hit `r` to regenerate |
| Typefully option missing | Check `echo $TYPEFULLY_API_KEY` |
| `Typefully API error 401` | Key is wrong or expired |

## Ideas for future extensions

- Cache the system prompt to reduce cost on repeated runs
- Correlate style with actual performance (after wiring up X Analytics)
- Simple FastAPI web UI for mobile access
- Thread mode (a connected series of tweets instead of a single post)
