import os
import asyncio
import random
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- CONFIG -----------------------------------------------------------------

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = os.getenv("DATABASE_URL", "miraforge.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            username TEXT,
            coins INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def get_or_create_user(tg_id: int, username: str | None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = cur.fetchone()

    if row is None:
        cur.execute(
            "INSERT INTO users (tg_id, username) VALUES (?, ?)",
            (tg_id, username or ""),
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = cur.fetchone()

    conn.close()
    return row


def update_user(tg_id: int, coins_delta: int = 0, xp_delta: int = 0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET coins = coins + ?, xp = xp + ?
        WHERE tg_id = ?
        """,
        (coins_delta, xp_delta, tg_id),
    )
    conn.commit()
    conn.close()


# --- HANDLERS ---------------------------------------------------------------

async def cmd_start(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username)
    text = (
        "🔥 Welcome to Miraplexity Autonomous Bot!\n\n"
        "You start with 100 coins and 0 XP.\n"
        "Use /profile to see your stats.\n"
        "Use /spin to gamble 10 coins and win XP + coins.\n"
    )
    await message.answer(text)


async def cmd_profile(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username)
    text = (
        f"👤 Profile\n\n"
        f"Username: @{message.from_user.username or 'unknown'}\n"
        f"Coins: {user['coins']}\n"
        f"XP: {user['xp']}"
    )
    await message.answer(text)


async def cmd_spin(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username)

    if user["coins"] < 10:
        await message.answer("You need at least 10 coins to spin. Use /profile to check.")
        return

    # Cost to spin
    update_user(message.from_user.id, coins_delta=-10)

    # Simple random reward
    prize_coins = random.choice([0, 5, 10, 20, 50])
    prize_xp = random.randint(5, 25)

    update_user(message.from_user.id, coins_delta=prize_coins, xp_delta=prize_xp)

    # Fetch updated user
    updated = get_or_create_user(message.from_user.id, message.from_user.username)

    text = (
        "🎰 Spin result!\n\n"
        f"You spent 10 coins.\n"
        f"Won: {prize_coins} coins and {prize_xp} XP.\n\n"
        f"New balance:\n"
        f"Coins: {updated['coins']}\n"
        f"XP: {updated['xp']}"
    )
    await message.answer(text)


async def cmd_help(message: types.Message):
    text = (
        "📜 Commands\n"
        "/start - register and get starting coins\n"
        "/profile - show your stats\n"
        "/spin - spend 10 coins to spin and win more\n"
        "/help - show this help\n"
    )
    await message.answer(text)


# --- BOOTSTRAP --------------------------------------------------------------

async def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Add it in Render environment variables."
        )

    init_db()

    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_profile, Command("profile"))
    dp.message.register(cmd_spin, Command("spin"))
    dp.message.register(cmd_help, Command("help"))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
