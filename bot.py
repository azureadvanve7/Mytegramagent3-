import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── APNI KEYS YAHAN DALO ──
TELEGRAM_TOKEN = "8215126734:AAFSk1yEgpf8IXbbKnA6F-cfj7w2UG5VrjQ"
ANTHROPIC_KEY  = "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"
# ── Anthropic Client ──
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SYSTEM_PROMPT = """Tu ek expert "Sarkari Yojana Bot" hai jo Indian government schemes aur documents ki jankari deta hai.

Rules:
1. Hamesha Hindi/Hinglish mein jawab de
2. Har jawab structured aur clear ho
3. Government schemes ke liye: naam, kya milta hai, kaun eligible hai, documents chahiye, website/helpline zaroor batao
4. Documents ke liye: poora process, kahan se banwayein, online ya offline, kitna time lagega
5. Jawab friendly aur helpful ho
6. Emojis use karo readable banane ke liye
7. Helpline numbers aur websites hamesha include karo
8. 200 words se zyada mat likho
9. Agar kuch nahi pata toh honestly kaho"""

# Har user ki chat history store karne ke liye
user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇮🇳 *Namaste! Sarkari Yojana Bot mein aapka swagat hai!*\n\n"
        "Main aapko sabhi government schemes aur documents ki jankari deta hoon — Hindi mein, bilkul free!\n\n"
        "Aap pooch sakte hain jaise:\n"
        "🌾 PM Kisan Yojana kya hai?\n"
        "🏥 Ayushman card kaise banta hai?\n"
        "🪪 Aadhaar update kaise karein?\n"
        "🏠 PM Awas Yojana ke liye apply kaise karein?\n\n"
        "Bas apna sawaal type karein! 👇",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Kya pooch sakte hain:*\n\n"
        "🌾 Kisan Yojnayein\n"
        "🏥 Swasthya Yojnayein\n"
        "🏠 Awas Yojnayein\n"
        "🎓 Shiksha Yojnayein\n"
        "💼 Rozgar Yojnayein\n"
        "📄 Sarkari Documents\n"
        "⚡ Bijli/Gas Yojnayein\n"
        "👴 Pension Yojnayein\n\n"
        "/start - Bot restart karein\n"
        "/reset - Chat history clear karein",
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("✅ Chat history clear ho gayi! Naya sawaal poochein.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # History initialize karein agar pehli baar hai
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # History mein user message add karein
    user_histories[user_id].append({
        "role": "user",
        "content": user_text
    })

    # Last 10 messages hi rakho (memory save karne ke liye)
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )

        reply = response.content[0].text

        # History mein bot reply add karein
        user_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            "🙏 Maafi chahta hoon! Abhi kuch technical problem aa rahi hai.\n"
            "Thodi der baad dobara try karein."
        )
        print(f"Error: {e}")

def main():
    print("🇮🇳 Sarkari Yojana Bot start ho raha hai...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot chal raha hai! Telegram pe check karein.")
    app.run_polling()

if __name__ == "__main__":
    main()
