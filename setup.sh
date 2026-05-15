#!/usr/bin/env bash
# Setup helper — checks dependencies and guides API key configuration.

set -e

echo "🔍 בודק התקנה…"

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 לא מותקן. התקן מ-python.org."
    exit 1
fi
echo "✓ Python: $(python3 --version)"

# anthropic SDK
if ! python3 -c "import anthropic" &> /dev/null; then
    echo "📦 מתקין anthropic SDK…"
    pip install --quiet anthropic
fi
echo "✓ anthropic SDK מותקן"

# API keys
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "⚠️  ANTHROPIC_API_KEY לא מוגדר."
    echo "   1. היכנס ל-https://console.anthropic.com/settings/keys"
    echo "   2. צור מפתח חדש"
    echo "   3. הרץ: export ANTHROPIC_API_KEY='sk-ant-...'"
    echo "   4. הוסף את השורה ל-~/.zshrc כדי שיהיה קבוע"
    echo ""
else
    echo "✓ ANTHROPIC_API_KEY מוגדר"
fi

if [ -z "$TYPEFULLY_API_KEY" ]; then
    echo ""
    echo "ℹ️  TYPEFULLY_API_KEY לא מוגדר (אופציונלי)."
    echo "   אם תרצה תזמון אוטומטי: typefully.com/settings/integrations"
    echo ""
else
    echo "✓ TYPEFULLY_API_KEY מוגדר"
fi

echo ""
echo "🚀 מוכן! נסה:"
echo "   python tweet_variations.py \"הרעיון הראשון שלי\""
