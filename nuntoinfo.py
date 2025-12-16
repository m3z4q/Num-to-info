import json
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# ================= CONFIG =================
BOT_TOKEN = "8206435813:AAGf_8lqQwT6MjDbz4HXNlZQf9cs03GofrY"
ADMIN_ID = 8472198541
FORCE_CHANNEL = "@TITANXPORTAL"

API_URL = "https://shaurya-said-baby-bubu-daba-du-pls.vercel.app/api"
API_KEY = "shauryaisdead"

DATA_FILE = "users.json"
# =========================================

# ---------- DATA ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "total_search": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=4)

data = load_data()

# ---------- FORCE JOIN ----------
async def is_joined(bot, user_id):
    try:
        m = await bot.get_chat_member(FORCE_CHANNEL, user_id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- ADMIN GIVE FLOW STATE ----------
give_state = {}  # admin_id -> {"step": 1/2, "target_uid": str}

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    if not await is_joined(context.bot, user.id):
        btn = [[InlineKeyboardButton("✅ Join Channel", url="https://t.me/TITANXPORTAL")]]
        await update.message.reply_text(
            "🚨 Bot use karne ke liye pehle channel join karo",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    is_new = uid not in data["users"]
    if is_new:
        data["users"][uid] = {"ref": 0, "used": 0}
        save_data(data)

        await context.bot.send_message(
            ADMIN_ID,
            f"🆕 New User Joined\n👤 {user.full_name}\n🆔 {user.id}"
        )

        # referral credit
        if context.args:
            ref_id = context.args[0]
            if ref_id in data["users"]:
                data["users"][ref_id]["ref"] += 1
                save_data(data)

    ref_link = f"https://t.me/{context.bot.username}?start={uid}"

    await update.message.reply_text(
        "📱 *Number Lookup Bot*\n\n"
        "🔹 Number bhejo (digits only)\n"
        "🔹 1 Refer = 1 Search\n\n"
        f"👤 Referrals: {data['users'][uid]['ref']}\n"
        f"🔍 Used: {data['users'][uid]['used']}\n\n"
        f"🔗 Your Refer Link:\n{ref_link}",
        parse_mode="Markdown"
    )

# ---------- LOOKUP ----------
async def lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    number = update.message.text.strip()

    if not number.isdigit():
        await update.message.reply_text("❌ Sirf digits bhejo")
        return

    user = data["users"].get(uid)
    if not user:
        return

    if user["used"] >= user["ref"]:
        await update.message.reply_text(
            "❌ Referral balance khatam\n🔗 Refer karke points lo"
        )
        return

    await update.message.reply_text("🔍 Searching...")

    try:
        params = {"key": API_KEY, "type": "mobile", "term": number}
        r = requests.get(API_URL, params=params, timeout=15)

        user["used"] += 1
        data["total_search"] += 1
        save_data(data)

        await update.message.reply_text(f"✅ Result:\n\n{r.text}")
    except:
        await update.message.reply_text("⚠️ API Error")

# ---------- STATS ----------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        f"📊 Bot Stats\n\n"
        f"👥 Users: {len(data['users'])}\n"
        f"🔍 Searches: {data['total_search']}"
    )

# ---------- BROADCAST ----------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Message missing")
        return

    sent = 0
    for uid in data["users"]:
        try:
            await context.bot.send_message(int(uid), msg)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")

# ---------- GIVE POINTS (ADMIN) ----------
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    give_state[ADMIN_ID] = {"step": 1}
    await update.message.reply_text("👤 User ID do")

async def handle_give_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    st = give_state.get(ADMIN_ID)
    if not st:
        return

    text = update.message.text.strip()

    # Step 1: receive user id
    if st["step"] == 1:
        if not text.isdigit():
            await update.message.reply_text("❌ Valid User ID do")
            return
        if text not in data["users"]:
            data["users"][text] = {"ref": 0, "used": 0}
            save_data(data)

        st["target_uid"] = text
        st["step"] = 2
        await update.message.reply_text("💎 Kitne points dene hain?")
        return

    # Step 2: receive points
    if st["step"] == 2:
        if not text.isdigit():
            await update.message.reply_text("❌ Sirf number (points) do")
            return

        pts = int(text)
        tgt = st["target_uid"]
        data["users"][tgt]["ref"] += pts
        save_data(data)

        # notify user
        try:
            await context.bot.send_message(
                int(tgt),
                f"🎁 Owner gives you {pts} points"
            )
        except:
            pass

        await update.message.reply_text(
            f"✅ {pts} points added to user {tgt}"
        )
        give_state.pop(ADMIN_ID, None)

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("give", give))

    # order matters: admin give flow first
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_give_flow))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lookup))

    print("🤖 Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
