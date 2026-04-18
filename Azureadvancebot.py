import os, re, json, tempfile, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import yt_dlp
import anthropic

BOT_TOKEN = os.environ["BOT_TOKEN"]
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """
You are an AI download agent inside Telegram.
Understand what the user wants and reply ONLY with JSON:

For video/music: {"action": "youtube", "query": "search term here"}
For PDF/book: {"action": "pdf", "query": "book name PDF free"}
For image: {"action": "image", "query": "description here"}
For normal chat: {"action": "chat", "reply": "your response"}

Reply with valid JSON only. Nothing else.
"""

def ask_ai(text):
    r = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}]
    )
    return r.content[0].text.strip()

def download_youtube(query):
    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "outtmpl": f"{tmp}/%(title)s.%(ext)s",
            "format": "best[filesize<45M]/best",
            "quiet": True,
            "noplaylist": True,
            "default_search": "ytsearch1",
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([query])
            files = os.listdir(tmp)
            if files:
                path = os.path.join(tmp, files[0])
                return open(path, "rb").read(), files[0]
    return None, None

def get_pdf(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(f"https://html.duckduckgo.com/html/?q={query.replace(' ','+')}", headers=headers, timeout=10)
        links = re.findall(r'https?://[^\s"<>]+\.pdf', r.text)
        if links:
            pr = requests.get(links[0], timeout=15, headers=headers)
            if pr.status_code == 200:
                return pr.content, links[0].split("/")[-1]
    except:
        pass
    return None, None

def get_image(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(f"https://html.duckduckgo.com/html/?q={query.replace(' ','+')}", headers=headers, timeout=10)
        links = re.findall(r'https?://[^\s"<>]+\.(?:jpg|jpeg|png)', r.text)
        if links:
            ir = requests.get(links[0], timeout=15, headers=headers)
            if ir.status_code == 200:
                return ir.content, "image.jpg"
    except:
        pass
    return None, None

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text("🤖 Working on it...")
    try:
        data = json.loads(ask_ai(text))
        action = data.get("action")

        if action == "youtube":
            await update.message.reply_text(f"🔍 Searching: {data['query']}")
            fb, fn = download_youtube(data["query"])
            if fb:
                await update.message.reply_document(fb, filename=fn, caption="✅ Done!")
            else:
                await update.message.reply_text("❌ Not found. Try different words.")

        elif action == "pdf":
            await update.message.reply_text(f"📄 Finding PDF: {data['query']}")
            fb, fn = get_pdf(data["query"])
            if fb:
                await update.message.reply_document(fb, filename=fn or "file.pdf", caption="✅ Here!")
            else:
                await update.message.reply_text("❌ PDF not found publicly.")

        elif action == "image":
            await update.message.reply_text(f"🖼️ Finding image: {data['query']}")
            fb, fn = get_image(data["query"])
            if fb:
                await update.message.reply_photo(fb, caption="✅ Here!")
            else:
                await update.message.reply_text("❌ Image not found.")

        elif action == "chat":
            await update.message.reply_text(data.get("reply", "I'm here!"))

    except Exception:
        await update.message.reply_text("⚠️ Something went wrong, try again!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("🚀 Bot is LIVE!")
    app.run_polling()
