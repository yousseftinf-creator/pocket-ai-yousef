import os
import logging
import asyncio
import yfinance as yf
import pandas as pd

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

ASSETS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "BTCUSD": "BTC-USD",
    "GOLD": "GC=F"
}


def analyze_market(symbol):

    data = yf.download(
        symbol,
        period="1d",
        interval="1m",
        progress=False
    )

    if data.empty or len(data) < 55:
        return "⚠️ لا توجد بيانات كافية للتحليل."

    close = data["Close"].squeeze()

    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))

    macd = (
        close.ewm(span=12).mean()
        - close.ewm(span=26).mean()
    )

    signal_line = macd.ewm(span=9).mean()

    price = float(close.iloc[-1])
    r = float(rsi.iloc[-1])

    e20 = float(ema20.iloc[-1])
    e50 = float(ema50.iloc[-1])

    m = float(macd.iloc[-1])
    s = float(signal_line.iloc[-1])

    result = "⏳ انتظار: لا توجد فرصة واضحة."

    if e20 > e50 and r > 50 and r < 68 and m > s:
        result = "🟢 CALL (شراء صعود)\n📈 الاتجاه صاعد."

    elif e20 < e50 and r < 50 and r > 32 and m < s:
        result = "🔴 PUT (شراء هبوط)\n📉 الاتجاه هابط."

    return f"""
🤖 Pocket AI Yousef

💹 الأصل: {symbol}

💰 السعر: {price:.5f}

📊 RSI: {r:.2f}

📈 EMA20: {e20:.5f}

📉 EMA50: {e50:.5f}

🧠 MACD: {m:.5f}

🔍 تحليل السوق:
{result}

⚠️ هذه إشارة تحليلية وليست ضماناً للربح.
🧪 استخدم الحساب التجريبي للاختبار.
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
🤖 أهلاً بك في Pocket AI Yousef

🇸🇦 مساعدك الذكي للتحليل باللغة العربية.

📊 /analyze EURUSD
📊 /analyze GBPUSD
₿ /analyze BTCUSD
🥇 /analyze GOLD

🧠 سأحلل السوق باستخدام:
📈 RSI
📉 EMA
📊 MACD

🛡️ الإصدار الحالي للتحليل فقط.
"""
    )


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "⚠️ اكتب اسم الأصل.\nمثال: /analyze EURUSD"
        )
        return

    asset = context.args[0].upper()

    if asset not in ASSETS:
        await update.message.reply_text(
            "❌ الأصل غير موجود في القائمة."
        )
        return

    await update.message.reply_text(
        "🔄 جارٍ تحليل السوق، انتظر قليلاً..."
    )

    try:
        result = await asyncio.to_thread(
            analyze_market,
            ASSETS[asset]
        )

        await update.message.reply_text(result)

    except Exception as error:
        logging.exception(error)

        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء تحليل السوق."
        )


def main():

    if not TOKEN:
        raise ValueError("لم يتم إعداد رمز البوت.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))

    print("Pocket AI Yousef is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
