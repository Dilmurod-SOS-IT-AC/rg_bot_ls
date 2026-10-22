from dotenv import load_dotenv
import os
import json

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
USERS_FILE = "users.json"

NAME, AGE, PHONE = 1, 2, 3



# ---------------------- DATABASE

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}  # no file yet -> no users
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


def is_admin(user_id):
    # ADMIN_ID comes from .env as text, Telegram ids are numbers -> compare as text
    return str(user_id) == str(ADMIN_ID)


# ---------------------- Commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.effective_user.id)

    if user_id in users:
        text = f"Welcome back, {users[user_id]['name']}! You are already registered.\nUse /me to see your data."
    else:
        text = "Hello, Welcome to this bot!\nUse /register to create your profile."

    if is_admin(user_id):
        text += "\n\nYou are the admin. Use /users to see everyone who registered."

    await update.message.reply_text(text)


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user = users.get(str(update.effective_user.id))

    if user is None:
        await update.message.reply_text("You are not registered yet. Use /register.")
        return

    text = (
        "Your profile:\n"
        f"Name: {user['name']}\n"
        f"Age: {user['age']}\n"
        f"Phone: {user['phone']}"
    )
    await update.message.reply_text(text)


async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # only the admin may see this list
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Sorry, this command is only for the admin.")
        return

    users = load_users()
    if not users:
        await update.message.reply_text("No registered users yet.")
        return

    lines = [f"Registered users: {len(users)}\n"]
    for number, (user_id, user) in enumerate(users.items(), start=1):
        username = f"@{user['username']}" if user.get("username") else "no username"
        lines.append(
            f"{number}. {user['name']}, {user['age']} y.o.\n"
            f"   Phone: {user['phone']}\n"
            f"   Telegram: {username} (id {user_id})"
        )

    # Telegram messages are limited to 4096 characters, so send in several parts
    message = ""
    for line in lines:
        if len(message) + len(line) + 1 > 4000:
            await update.message.reply_text(message)
            message = ""
        message += line + "\n"
    if message:
        await update.message.reply_text(message)


# ---------------------- Registration (step by step)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if str(update.effective_user.id) in users:
        await update.message.reply_text("You are already registered. Use /me to see your data.")
        return ConversationHandler.END

    await update.message.reply_text("Let's register you!\nWhat is your name?\n\n(Send /cancel to stop.)")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("The name is too short. Please type your name again:")
        return NAME  # stay on this step

    context.user_data["name"] = name
    await update.message.reply_text("Nice to meet you! How old are you?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or not 1 <= int(text) <= 120:
        await update.message.reply_text("Please send your age as a number, for example: 25")
        return AGE

    context.user_data["age"] = int(text)
    await update.message.reply_text("Great! Now send your phone number, for example: +998901234567")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    digits = phone.replace("+", "", 1).replace(" ", "")
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        await update.message.reply_text("That does not look like a phone number. Try again, for example: +998901234567")
        return PHONE

    # everything collected -> save the user in the json file
    user = update.effective_user
    users = load_users()
    users[str(user.id)] = {
        "name": context.user_data["name"],
        "age": context.user_data["age"],
        "phone": phone,
        "username": user.username,
    }
    save_users(users)

    context.user_data.clear()
    await update.message.reply_text("You are registered. Thank you! Use /me to see your data.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Registration cancelled. Send /register to start again.")
    return ConversationHandler.END


# ---------------------- Main
def main():
    if not BOT_TOKEN or not ADMIN_ID:
        print("Please set BOT_TOKEN and ADMIN_ID in the .env file (see .env.example).")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # filters.TEXT & ~filters.COMMAND = normal text messages, but not /commands
    text_only = filters.TEXT & ~filters.COMMAND

    registration = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            NAME: [MessageHandler(text_only, get_name)],
            AGE: [MessageHandler(text_only, get_age)],
            PHONE: [MessageHandler(text_only, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(registration)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
