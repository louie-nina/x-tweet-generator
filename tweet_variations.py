#!/usr/bin/env python3
"""
Tweet Variations Generator + Scheduler
---------------------------------------
לוקח רעיון/נושא ומחזיר 5 וריאציות טוויט מוכנות לפרסום ב-X,
מאפשר לבחור אחת מהן, ושומר היסטוריה לניתוח דפוסים.
אופציונלית — מתזמן אוטומטית דרך Typefully.

כל הטוויטים נוצרים באנגלית, ללא קשר לשפת הקלט.

שימוש:
    python tweet_variations.py "הרעיון שלך"
    python tweet_variations.py "your idea in English"
    python tweet_variations.py --history
    python tweet_variations.py --stats

דרישות:
    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."

אופציונלי לתזמון אוטומטי:
    export TYPEFULLY_API_KEY="..."  (מ-typefully.com/settings/integrations)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

import anthropic

MODEL = "claude-opus-4-7"
HISTORY_FILE = Path(__file__).parent / "history.csv"
TYPEFULLY_API = "https://api.typefully.com/v1/drafts/"

# ---------- ANSI colors (no extra deps) ----------
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    GRAY = "\033[90m"


STYLE_META = {
    "hook":     {"icon": "🪝", "label": "Hook",     "color": C.MAGENTA},
    "story":    {"icon": "📖", "label": "Story",    "color": C.BLUE},
    "list":     {"icon": "📋", "label": "List",     "color": C.GREEN},
    "question": {"icon": "❓", "label": "Question", "color": C.YELLOW},
    "insight":  {"icon": "💡", "label": "Insight",  "color": C.CYAN},
}

SYSTEM_PROMPT = """You are a world-class X (Twitter) ghostwriter who helps creators grow their audience.

Given a raw idea, produce 5 distinct tweet variations. Each must:
- Stand alone (no thread, no "1/")
- Be under 280 characters
- Have a strong hook in the first line
- Use line breaks for readability when helpful
- Avoid hashtags unless they add real value
- Avoid emojis unless they fit the tone
- Sound human, not corporate
- Not start with "I" if avoidable — too generic

The 5 variations MUST each take a different angle, in this order:
1. **hook**     — bold claim or contrarian take
2. **story**    — personal anecdote / mini-narrative
3. **list**     — short numbered or bulleted insights
4. **question** — provocative question that invites replies
5. **insight**  — clear, valuable lesson stated plainly

LANGUAGE: Always write the tweets in English, regardless of the language of the input idea. If the user writes the idea in Hebrew or any other language, translate the concept and produce English tweets."""

SCHEMA = {
    "type": "object",
    "properties": {
        "variations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "style":      {"type": "string", "enum": ["hook", "story", "list", "question", "insight"]},
                    "tweet":      {"type": "string"},
                    "char_count": {"type": "integer"},
                },
                "required": ["style", "tweet", "char_count"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["variations"],
    "additionalProperties": False,
}


# ---------- Generation ----------
def generate_variations(idea: str) -> list[dict]:
    """Call Claude and return a list of 5 variation dicts (all in English)."""
    client = anthropic.Anthropic()

    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[
            {"role": "user", "content": f"Generate 5 tweet variations for this idea:\n\n{idea}"}
        ],
    ) as stream:
        message = stream.get_final_message()

    text = next(b.text for b in message.content if b.type == "text")
    data = json.loads(text)
    return data["variations"]


# ---------- Display ----------
def render_variation(idx: int, v: dict) -> str:
    meta = STYLE_META.get(v["style"], {"icon": "•", "label": v["style"], "color": C.GRAY})
    over = " " + C.RED + "⚠ OVER 280" + C.RESET if v["char_count"] > 280 else ""
    header = f"{meta['color']}{C.BOLD}#{idx}  {meta['icon']} {meta['label']}{C.RESET}  {C.DIM}({v['char_count']} chars){C.RESET}{over}"
    sep = C.GRAY + "─" * 60 + C.RESET
    return f"{sep}\n{header}\n{sep}\n{v['tweet']}\n"


def show_variations(variations: list[dict]) -> None:
    print()
    for i, v in enumerate(variations, 1):
        print(render_variation(i, v))


# ---------- History ----------
def save_to_history(idea: str, variation: dict, action: str, scheduled_for: str = "") -> None:
    """Append the chosen variation to history.csv."""
    new_file = not HISTORY_FILE.exists()
    with HISTORY_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "idea", "style", "char_count", "tweet", "action", "scheduled_for"])
        writer.writerow([
            dt.datetime.now().isoformat(timespec="seconds"),
            idea,
            variation["style"],
            variation["char_count"],
            variation["tweet"],
            action,
            scheduled_for,
        ])


def show_history(limit: int = 20) -> None:
    if not HISTORY_FILE.exists():
        print(f"{C.DIM}אין עדיין היסטוריה. הרץ generate כדי להתחיל.{C.RESET}")
        return
    with HISTORY_FILE.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"\n{C.BOLD}היסטוריה — {len(rows)} פוסטים סה\"כ (מציג {min(limit, len(rows))} אחרונים){C.RESET}\n")
    for row in rows[-limit:]:
        meta = STYLE_META.get(row["style"], {"icon": "•", "label": row["style"], "color": C.GRAY})
        ts = row["timestamp"].replace("T", " ")[:16]
        action_color = C.GREEN if row["action"] == "scheduled" else C.YELLOW if row["action"] == "posted" else C.DIM
        print(f"{C.GRAY}{ts}{C.RESET}  {meta['color']}{meta['icon']} {meta['label']:8}{C.RESET}  "
              f"{action_color}{row['action']:10}{C.RESET}  {row['tweet'][:70]}{'…' if len(row['tweet']) > 70 else ''}")
    print()


def show_stats() -> None:
    if not HISTORY_FILE.exists():
        print(f"{C.DIM}אין עדיין נתונים לסטטיסטיקה.{C.RESET}")
        return
    with HISTORY_FILE.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"{C.DIM}אין עדיין נתונים לסטטיסטיקה.{C.RESET}")
        return

    style_counts = Counter(r["style"] for r in rows)
    action_counts = Counter(r["action"] for r in rows)
    avg_len = sum(int(r["char_count"]) for r in rows) / len(rows)

    print(f"\n{C.BOLD}סטטיסטיקה ({len(rows)} פוסטים){C.RESET}\n")
    print(f"{C.BOLD}לפי סגנון:{C.RESET}")
    for style, count in style_counts.most_common():
        meta = STYLE_META.get(style, {"icon": "•", "label": style, "color": C.GRAY})
        bar = "█" * count
        pct = 100 * count / len(rows)
        print(f"  {meta['color']}{meta['icon']} {meta['label']:10}{C.RESET}  {bar} {C.DIM}{count} ({pct:.0f}%){C.RESET}")

    print(f"\n{C.BOLD}לפי פעולה:{C.RESET}")
    for action, count in action_counts.most_common():
        print(f"  {action:12}  {count}")

    print(f"\n{C.BOLD}אורך ממוצע:{C.RESET}  {avg_len:.0f} chars\n")


# ---------- Typefully integration ----------
def schedule_via_typefully(tweet: str, schedule_date: str = "next-free-slot") -> dict:
    """Schedule a tweet via Typefully API. Returns the draft response."""
    api_key = os.environ.get("TYPEFULLY_API_KEY")
    if not api_key:
        raise RuntimeError("TYPEFULLY_API_KEY not set")

    body = json.dumps({
        "content": tweet,
        "schedule_date": schedule_date,
    }).encode("utf-8")

    req = urllib.request.Request(
        TYPEFULLY_API,
        data=body,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Typefully API error {e.code}: {detail}") from e


# ---------- Interactive flow ----------
def interactive_select(variations: list[dict], idea: str) -> None:
    """Show variations, let user pick + save + optionally schedule."""
    while True:
        show_variations(variations)
        has_typefully = bool(os.environ.get("TYPEFULLY_API_KEY"))
        tf_hint = "" if has_typefully else f"  {C.DIM}(set TYPEFULLY_API_KEY for auto-scheduling){C.RESET}"
        print(f"{C.BOLD}מה הלאה?{C.RESET}{tf_hint}")
        print(f"  {C.CYAN}1-5{C.RESET}  בחר וריאציה")
        print(f"  {C.CYAN}r{C.RESET}    הרץ מחדש (וריאציות חדשות)")
        print(f"  {C.CYAN}q{C.RESET}    יציאה ללא שמירה\n")

        choice = input(f"{C.BOLD}בחירה: {C.RESET}").strip().lower()

        if choice == "q":
            print(f"{C.DIM}יציאה. לא נשמר כלום.{C.RESET}")
            return
        if choice == "r":
            print(f"\n{C.DIM}⏳ מייצר וריאציות חדשות…{C.RESET}\n")
            variations = generate_variations(idea)
            continue
        if choice not in {"1", "2", "3", "4", "5"}:
            print(f"{C.RED}לא הבנתי. נסה שוב.{C.RESET}")
            continue

        chosen = variations[int(choice) - 1]
        print(f"\n{C.GREEN}✓ נבחר #{choice}{C.RESET}\n")
        post_action(chosen, idea)
        return


def post_action(variation: dict, idea: str) -> None:
    """Ask what to do with the chosen variation."""
    has_tf = bool(os.environ.get("TYPEFULLY_API_KEY"))

    print(f"{C.BOLD}מה לעשות איתו?{C.RESET}")
    print(f"  {C.CYAN}s{C.RESET}  שמור להיסטוריה בלבד (תוכל להעתיק ולפרסם ידני)")
    if has_tf:
        print(f"  {C.CYAN}n{C.RESET}  תזמן ל-Typefully בחריץ הבא הפנוי")
        print(f"  {C.CYAN}d{C.RESET}  תזמן ל-Typefully בתאריך ספציפי (ISO 8601)")
    print(f"  {C.CYAN}c{C.RESET}  רק העתק (הדפס במסוף לעותק מהיר)\n")

    action = input(f"{C.BOLD}פעולה: {C.RESET}").strip().lower() or "s"

    if action == "s":
        save_to_history(idea, variation, action="saved")
        print(f"{C.GREEN}✓ נשמר ב-{HISTORY_FILE.name}{C.RESET}")
    elif action == "c":
        print(f"\n{C.BOLD}הטוויט:{C.RESET}\n{variation['tweet']}\n")
        save_to_history(idea, variation, action="copied")
        print(f"{C.GREEN}✓ נשמר ב-{HISTORY_FILE.name}{C.RESET}")
    elif action == "n" and has_tf:
        try:
            resp = schedule_via_typefully(variation["tweet"], "next-free-slot")
            scheduled_for = resp.get("scheduled_date", "next-free-slot")
            save_to_history(idea, variation, action="scheduled", scheduled_for=scheduled_for)
            print(f"{C.GREEN}✓ תוזמן ל-Typefully{C.RESET}  {C.DIM}(scheduled_date: {scheduled_for}){C.RESET}")
            if "share_url" in resp:
                print(f"  {C.DIM}{resp['share_url']}{C.RESET}")
        except RuntimeError as e:
            print(f"{C.RED}✗ תזמון נכשל: {e}{C.RESET}")
            save_to_history(idea, variation, action="saved")
            print(f"{C.YELLOW}נשמר להיסטוריה כגיבוי.{C.RESET}")
    elif action == "d" and has_tf:
        when = input(f"מתי? (ISO 8601, למשל 2026-05-20T09:00:00Z): ").strip()
        try:
            resp = schedule_via_typefully(variation["tweet"], when)
            save_to_history(idea, variation, action="scheduled", scheduled_for=when)
            print(f"{C.GREEN}✓ תוזמן ל-{when}{C.RESET}")
            if "share_url" in resp:
                print(f"  {C.DIM}{resp['share_url']}{C.RESET}")
        except RuntimeError as e:
            print(f"{C.RED}✗ תזמון נכשל: {e}{C.RESET}")
            save_to_history(idea, variation, action="saved")
    else:
        print(f"{C.YELLOW}לא הבנתי. שומר להיסטוריה כברירת מחדל.{C.RESET}")
        save_to_history(idea, variation, action="saved")


# ---------- Main ----------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate 5 tweet variations and optionally schedule them.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("idea", nargs="?", help="The idea/topic. If omitted, reads from stdin.")
    parser.add_argument("--history", action="store_true", help="Show recent history and exit")
    parser.add_argument("--stats", action="store_true", help="Show style statistics and exit")
    parser.add_argument("--limit", type=int, default=20, help="History limit (default: 20)")
    args = parser.parse_args()

    if args.history:
        show_history(args.limit)
        return 0
    if args.stats:
        show_stats()
        return 0

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"{C.RED}Error: set ANTHROPIC_API_KEY environment variable.{C.RESET}", file=sys.stderr)
        print(f"{C.DIM}    export ANTHROPIC_API_KEY='sk-ant-...'{C.RESET}", file=sys.stderr)
        return 1

    idea = args.idea
    if not idea:
        if sys.stdin.isatty():
            print(f"{C.BOLD}הזן את הרעיון שלך{C.RESET} {C.DIM}(Enter פעמיים לסיום):{C.RESET}")
            lines = []
            try:
                while True:
                    line = input()
                    if not line and lines and not lines[-1]:
                        break
                    lines.append(line)
            except EOFError:
                pass
            idea = "\n".join(lines).strip()
        else:
            idea = sys.stdin.read().strip()

    if not idea:
        print(f"{C.RED}Error: no idea provided.{C.RESET}", file=sys.stderr)
        return 1

    preview = idea[:60] + ("…" if len(idea) > 60 else "")
    print(f"\n{C.DIM}⏳ מייצר 5 וריאציות עבור: {preview}{C.RESET}")

    try:
        variations = generate_variations(idea)
    except anthropic.APIError as e:
        print(f"{C.RED}API error: {e.message}{C.RESET}", file=sys.stderr)
        return 1

    interactive_select(variations, idea)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{C.DIM}יציאה.{C.RESET}")
        sys.exit(130)
