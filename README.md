# Registration bot

A Telegram bot that registers users (name, age, phone) and saves them in `users.json`.
The admin can list everyone with `/users`.

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Find your own Telegram user id (for example with [@userinfobot](https://t.me/userinfobot)).
3. Copy `.env.example` to `.env` and fill in both values:
   ```
   BOT_TOKEN=123456:ABC...
   ADMIN_ID=123456789
   ```
4. Install and run:
   ```
   pip install -r requirements.txt
   python bot.py
   ```

## Commands

| Command     | Who    | What it does                          |
|-------------|--------|---------------------------------------|
| `/start`    | anyone | greeting                              |
| `/register` | anyone | asks name, age, phone and saves them  |
| `/cancel`   | anyone | stops the registration                |
| `/me`       | anyone | shows your saved data                 |
| `/users`    | admin  | lists all registered users            |
