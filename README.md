# Tweet Variations Generator + Scheduler

מערכת מלאה ליצירת תוכן ל-X (טוויטר):
- 🤖 לוקח רעיון (בעברית או אנגלית) → מחזיר **5 וריאציות באנגלית** בזוויות שונות (Hook / Story / List / Question / Insight)
- 🎯 בחירה אינטראקטיבית עם אפשרות "הרץ מחדש"
- 📊 **היסטוריה אוטומטית** ב-CSV + סטטיסטיקות לפי סגנון
- 📅 **תזמון אוטומטי** דרך Typefully (אופציונלי)
- 🌐 אפשר לכתוב את הרעיון בעברית — הטוויטים תמיד באנגלית

## התקנה מהירה (3 שלבים)

```bash
# 1. התקנה
pip install anthropic

# 2. מפתח חובה (מ-console.anthropic.com)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. אופציונלי — לתזמון אוטומטי (מ-typefully.com/settings/integrations)
export TYPEFULLY_API_KEY="..."
```

טיפ: הוסף את ה-`export`-ים ל-`~/.zshrc` כדי שזה יהיה קבוע.

## שימוש

### יצירת וריאציות
```bash
python tweet_variations.py "מה למדתי השנה על בנייה של מוצרים"
```

תקבל 5 וריאציות, ואז:
- **1–5** — בחר וריאציה
- **r** — הרץ שוב לקבל 5 חדשות
- **q** — צא בלי לשמור

אחרי שבחרת:
- **s** — שמור להיסטוריה (ברירת מחדל)
- **c** — הדפס לעותק מהיר + שמור
- **n** — תזמן ב-Typefully בחריץ הבא הפנוי *(אם הגדרת מפתח)*
- **d** — תזמן לתאריך ספציפי *(אם הגדרת מפתח)*

### אפשר לכתוב את הרעיון בעברית
הטוויטים תמיד יחזרו באנגלית, גם אם תכתוב את הרעיון בעברית:

```bash
python tweet_variations.py "המחשבה שלי על אוטומציה ושיווק"
# → 5 tweets in English

# מצב אינטראקטיבי לרעיון ארוך
python tweet_variations.py
# (הקלד את הרעיון, Enter פעמיים לסיום)
```

### צפייה בהיסטוריה וסטטיסטיקות
```bash
python tweet_variations.py --history          # 20 אחרונים
python tweet_variations.py --history --limit 50

python tweet_variations.py --stats            # פילוח לפי סגנון + פעולה
```

## דוגמת פלט

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

## קבצים שהמערכת יוצרת

- `history.csv` — היסטוריה מלאה (timestamp, idea, style, char_count, tweet, action, scheduled_for)
- אין בסיס נתונים — הכל פשוט בקובץ אחד שאפשר לפתוח ב-Excel/Numbers

## ארכיטקטורה — איך זה עובד מאחורי הקלעים

1. **מודל:** `claude-opus-4-7` עם streaming (למניעת timeouts)
2. **Structured outputs:** JSON schema מבטיח שתמיד יחזרו בדיוק 5 וריאציות בפורמט תקין — אין parsing שבור
3. **System prompt:** מנחה את המודל לחמש זוויות ספציפיות + מגביל באורך, ללא hashtags/emojis מיותרים
4. **Typefully API:** קריאת REST פשוטה (`urllib`, ללא תלויות נוספות), תומך ב-`next-free-slot` או ISO 8601

## פתרון בעיות

| בעיה | פתרון |
|------|--------|
| `ANTHROPIC_API_KEY not set` | `export ANTHROPIC_API_KEY="sk-ant-..."` |
| הוריאציה מעל 280 תווים | יופיע סימן ⚠️ — תקן ידנית או בקש `r` להרצה חדשה |
| Typefully לא מופיע באפשרויות | בדוק `echo $TYPEFULLY_API_KEY` |
| `Typefully API error 401` | המפתח שגוי או פג תוקף |

## מה הלאה (רעיונות להרחבה)

- Cache prompt על system message כדי לחסוך עלות בריצות חוזרות
- ניתוח קורלציה בין סגנון לבין ביצועים בפועל (לאחר חיבור ל-X Analytics)
- Web UI פשוט עם FastAPI אם רוצים גישה מהנייד
- מצב thread (סדרת טוויטים מקושרת) במקום פוסט בודד
