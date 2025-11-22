import os
import random
from uuid import uuid4
from supabase import create_client
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# ============ CONFIG FROM ENV ============
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not SUPABASE_URL or not SUPABASE_KEY or not BOT_TOKEN:
    raise RuntimeError("Missing SUPABASE_URL, SUPABASE_KEY, or TELEGRAM_BOT_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============ HELPERS ============
def get_tournament_by_name(name):
    res = supabase.table("tournaments").select("*").eq("name", name).execute()
    return res.data[0] if res.data else None


def get_players_for_tournament(tourney_id):
    return supabase.table("players").select("*").eq("tournament_id", tourney_id).execute().data


def update_winner_stats(player):
    new_xp = player["xp"] + 10
    new_level = 1 + (new_xp // 100)
    new_skill = player["skill_rating"] + 5

    supabase.table("players").update({
        "xp": new_xp,
        "level": new_level,
        "skill_rating": new_skill
    }).eq("id", player["id"]).execute()

    return new_xp, new_level, new_skill


async def auto_update_leaderboard(tournament_name, chat_id, app):
    tourney = get_tournament_by_name(tournament_name)
    if not tourney:
        await app.bot.send_message(chat_id=chat_id, text=f"Tournament '{tournament_name}' not found.")
        return
    
    players = supabase.table("players").select("*") \
        .eq("tournament_id", tourney["id"]) \
        .order("skill_rating", desc=True).execute().data

    spotlight = "🏆 Top 3 Players:\n"
    for i, p in enumerate(players[:3]):
        spotlight += f"{i+1}. {p['username']} - Level {p['level']}, XP {p['xp']}, Skill {p['skill_rating']}\n"

    total_pool = float(tourney["prize_pool"])
    top10_pool = total_pool * 0.75
    total_weight = sum(range(1, 11))

    payouts_msg = "\n💰 Top 10 Payouts:\n"
    for i, player in enumerate(players[:10]):
        weight = 10 - i
        payout = round((weight / total_weight) * top10_pool, 2)
        payouts_msg += f"{i+1}. {player['username']} → ${payout}\n"

    await app.bot.send_message(chat_id=chat_id, text=spotlight + payouts_msg)


async def auto_match_round(tournament_name, chat_id, app):
    tourney = get_tournament_by_name(tournament_name)
    players = get_players_for_tournament(tourney["id"])

    if len(players) < 2:
        await app.bot.send_message(chat_id=chat_id, text=f"Not enough players in {tournament_name}.")
        return

    random.shuffle(players)
    pairs = [(players[i], players[i+1]) for i in range(0, len(players) - 1, 2)]

    for p1, p2 in pairs:
        score1 = p1["skill_rating"] + random.randint(0, 10)
        score2 = p2["skill_rating"] + random.randint(0, 10)
        winner = p1 if score1 >= score2 else p2

        supabase.table("matches").insert({
            "id": str(uuid4()),
            "tournament_id": tourney["id"],
            "player1": p1["id"],
            "player2": p2["id"],
            "winner": winner["id"]
        }).execute()

        new_xp, new_level, new_skill = update_winner_stats(winner)

        await app.bot.send_message(
            chat_id=chat_id,
            text=f"🎱 {p1['username']} vs {p2['username']} → Winner: {winner['username']} "
                 f"(XP {new_xp}, Level {new_level}, Skill {new_skill})"
        )

    await auto_update_leaderboard(tournament_name, chat_id, app)


# ============ COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Miraplexity is LIVE.\n"
        "/join <TournamentName>\n"
        "/leaderboard <TournamentName>\n"
        "/payouts <TournamentName>\n"
        "/auto <TournamentName> (runs every 60s)"
    )


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /join <TournamentName>")
        return

    username = update.effective_user.first_name or update.effective_user.username or f"User{update.effective_user.id}"
    tournament_name = " ".join(context.args)

    tourney = get_tournament_by_name(tournament_name)
    if not tourney:
        await update.message.reply_text(f"Tournament '{tournament_name}' not found.")
        return

    # Check if player already joined this tournament
    user_id = update.effective_user.id
    existing = supabase.table("players").select("*") \
        .eq("tournament_id", tourney["id"]) \
        .eq("username", username).execute().data
    
    if existing:
        await update.message.reply_text(f"You've already joined {tournament_name}!")
        return

    supabase.table("players").insert({
        "id": str(uuid4()),
        "username": username,
        "xp": 0,
        "level": 1,
        "skill_rating": 100,
        "wallet": 0,
        "tournament_id": tourney["id"]
    }).execute()

    new_pool = tourney["prize_pool"] + tourney["entry_fee"]
    supabase.table("tournaments").update({"prize_pool": new_pool}).eq("id", tourney["id"]).execute()

    await update.message.reply_text(f"{username} joined {tournament_name}! Prize pool now: ${new_pool}")


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /leaderboard <TournamentName>")
        return

    tournament_name = " ".join(context.args)
    await auto_update_leaderboard(tournament_name, update.effective_chat.id, context.application)


async def payouts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /payouts <TournamentName>")
        return

    tournament_name = " ".join(context.args)
    tourney = get_tournament_by_name(tournament_name)
    if not tourney:
        await update.message.reply_text(f"Tournament '{tournament_name}' not found.")
        return
    
    players = supabase.table("players").select("*") \
        .eq("tournament_id", tourney["id"]).order("skill_rating", desc=True).execute().data

    total_pool = float(tourney["prize_pool"])
    top10_pool = total_pool * 0.75
    total_weight = sum(range(1, 11))

    msg = f"💰 Top 10 payouts for {tournament_name}:\n"
    for i, p in enumerate(players[:10]):
        weight = 10 - i
        payout = round((weight / total_weight) * top10_pool, 2)
        msg += f"{i+1}. {p['username']} → ${payout}\n"

    await update.message.reply_text(msg)


async def auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /auto <TournamentName>")
        return

    tournament_name = " ".join(context.args)
    chat_id = update.effective_chat.id

    job_queue = context.application.job_queue

    job_queue.run_repeating(
        auto_job,
        interval=60,
        first=5,
        data={"tournament_name": tournament_name, "chat_id": chat_id}
    )

    await update.message.reply_text(f"Auto-mode started for {tournament_name}!")


async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    tournament_name = data["tournament_name"]
    chat_id = data["chat_id"]

    await auto_match_round(tournament_name, chat_id, context.application)


# ============ MAIN ============
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("payouts", payouts))
    app.add_handler(CommandHandler("auto", auto_cmd))

    print("Miraplexity Bot LIVE...")
    app.run_polling()


if __name__ == "__main__":
    main()
