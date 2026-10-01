import json, os, math
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ================= CONFIG =================
BOT_TOKEN = "8663164385:AAHRn4INDGEGZO4mH4tW6O-ZyOQw83Va1ZQ"
FORCE_JOIN = "@duvkuppp"
VIDEO_CHANNEL = "@dudhwalla"
PAID_WEBSITE = "https://yourwebsite.com/subscribe"
ADMINS = {6567632240}
DATA_FILE = "data.json"
ITEMS_PER_PAGE = 5
# =========================================

# ============ REPLIT KEEP ALIVE ============
app = Flask("")

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    app.run(host="0.0.0.0", port=8080)
# =========================================

# ============== STORAGE ===================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"videos": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2, ensure_ascii=False)

DATA = load_data()
VIDEOS = DATA["videos"]
# =========================================

# ============== HELPERS ===================
def is_admin(uid):
    return uid in ADMINS

async def is_joined(bot, uid):
    try:
        m = await bot.get_chat_member(FORCE_JOIN, uid)
        return m.status in ("member", "administrator", "creator")
    except:
        return False
# =========================================

# ============== UI ========================
def join_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔔 Join Our Official Channel to Continue",
            url=f"https://t.me/{FORCE_JOIN.lstrip('@')}"
        )],
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Top Viral Videos", callback_data="topviral_1"),
         InlineKeyboardButton("🆕 Recently Added", callback_data="recent_1")],
        [InlineKeyboardButton("🎬 Movies Collection", callback_data="movies_1"),
         InlineKeyboardButton("🚀 Viral Clips", callback_data="viral_1")],
        [InlineKeyboardButton(
            "📺 Join Our Official Video Channel\n(Get all uploads instantly)",
            url=f"https://t.me/{VIDEO_CHANNEL.lstrip('@')}"
        )],
        [InlineKeyboardButton("🔒 Premium Content", callback_data="premium")]
    ])

def paginate(key, page, total):
    row = []
    if page > 1:
        row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"{key}_{page-1}"))
    if page < total:
        row.append(InlineKeyboardButton("➡️ Next", callback_data=f"{key}_{page+1}"))
    return row
# =========================================

# ============== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(context.bot, update.effective_user.id):
        await update.message.reply_text(
            "🔒 *Access Restricted*\n\n"
            "To access our video library, you must first join our official channel.\n\n"
            "Once joined, tap **I Joined** to continue.",
            reply_markup=join_markup(),
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "🎬 *Welcome to the Official Video Hub*\n\n"
        "🔥 Top Viral videos are curated and shown first.\n"
        "📺 Join our official channel to never miss any upload.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )
# =========================================

# =========== JOIN CHECK ===================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if await is_joined(context.bot, q.from_user.id):
        await q.edit_message_text(
            "✅ *Access Granted*\n\nEnjoy browsing videos.",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    else:
        await q.answer("❌ Please join the channel first.", show_alert=True)
# =========================================

# ============== MENU ======================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    key, page = q.data.split("_")
    page = int(page)

    if key == "premium":
        await q.edit_message_text(
            "🔒 *Premium Content*\n\n"
            "Premium videos are available on our website.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Unlock Premium", url=PAID_WEBSITE)],
                [InlineKeyboardButton("⬅️ Back", callback_data="back")]
            ]),
            parse_mode="Markdown"
        )
        return

    if key == "recent":
        items = VIDEOS[::-1]
    elif key == "topviral":
        items = [v for v in VIDEOS if v.get("top_viral")]
    else:
        items = [v for v in VIDEOS if v["category"] == key]

    if not items:
        await q.edit_message_text("No videos available.", reply_markup=main_menu())
        return

    total = max(1, math.ceil(len(items) / ITEMS_PER_PAGE))
    page_items = items[(page-1)*ITEMS_PER_PAGE: page*ITEMS_PER_PAGE]

    buttons = []
    for v in page_items:
        title = v.get("caption", "▶️ Watch Video")
        if v.get("top_viral"):
            title = "🔥 " + title
        buttons.append([InlineKeyboardButton(title[:50], callback_data=f"play_{v['msg_id']}")])

    nav = paginate(key, page, total)
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back")])

    await q.edit_message_text(
        f"📄 Page {page}/{total}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
# =========================================

# ============== PLAY ======================
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    msg_id = int(q.data.split("_")[1])

    await context.bot.forward_message(
        chat_id=q.message.chat_id,
        from_chat_id=VIDEO_CHANNEL,
        message_id=msg_id
    )
# =========================================

# ========== ADMIN UPLOAD ==================
async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    sent = await context.bot.copy_message(
        chat_id=VIDEO_CHANNEL,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )

    context.user_data["msg_id"] = sent.message_id

    await update.message.reply_text(
        "🛠 *Admin Setup*\n\n"
        "Select category and options:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Movies", callback_data="set_movies"),
             InlineKeyboardButton("🚀 Viral", callback_data="set_viral")],
            [InlineKeyboardButton("🔥 Mark as Top Viral", callback_data="set_topviral")]
        ]),
        parse_mode="Markdown"
    )
# =========================================

# ========== SET CATEGORY ==================
async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    msg_id = context.user_data.get("msg_id")
    action = q.data.replace("set_", "")

    if not msg_id:
        return

    context.user_data["category"] = action

    await q.edit_message_text(
        "✍️ *Add a caption for this video*\n\n"
        "Send caption now, or skip.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Skip Caption", callback_data="skip_caption")]
        ]),
        parse_mode="Markdown"
    )
# =========================================

# ========== CAPTION =======================
async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if "msg_id" not in context.user_data:
        return

    caption = update.message.text
    await apply_caption(update, context, caption)

async def skip_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await apply_caption(update.callback_query, context, "")

async def apply_caption(src, context, caption):
    msg_id = context.user_data["msg_id"]
    category = context.user_data.get("category", "viral")

    if caption:
        await context.bot.edit_message_caption(
            chat_id=VIDEO_CHANNEL,
            message_id=msg_id,
            caption=caption
        )

    VIDEOS.append({
        "msg_id": msg_id,
        "category": category,
        "caption": caption,
        "top_viral": category == "topviral"
    })
    save_data()
    context.user_data.clear()

    if hasattr(src, "edit_message_text"):
        await src.edit_message_text("✅ Video published successfully.")
    else:
        await src.message.reply_text("✅ Video published successfully.")
# =========================================

# ============== BACK ======================
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🎬 Video Hub",
        reply_markup=main_menu()
    )
# =========================================

# ============== RUN =======================
def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    app_bot.add_handler(CallbackQueryHandler(menu, pattern="^(topviral|recent|movies|viral)_"))
    app_bot.add_handler(CallbackQueryHandler(play, pattern="^play_"))
    app_bot.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, admin_upload))
    app_bot.add_handler(CallbackQueryHandler(set_category, pattern="^set_"))
    app_bot.add_handler(CallbackQueryHandler(skip_caption, pattern="^skip_caption$"))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption))
    app_bot.add_handler(CallbackQueryHandler(back, pattern="^back$"))

    print("Bot running on Replit…")
    app_bot.run_polling()

# =========================================
if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_web).start()
    run_bot()
