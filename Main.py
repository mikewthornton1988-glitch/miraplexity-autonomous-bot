import os, asyncio, random, sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
DB="miraforge.db"def conn():
    return sqlite3.connect(DB)

def init_db():
    c=conn(); cur=c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        tg_id INTEGER UNIQUE,
        username TEXT,
        coins INTEGER DEFAULT 100,
        xp INTEGER DEFAULT 0
    )""")
    c.commit(); c.close()def get_user(tg_id, username):
    c=conn(); cur=c.cursor()
    cur.execute("SELECT tg_id,username,coins,xp FROM users WHERE tg_id=?",(tg_id,))
    r=cur.fetchone()
    if r: c.close(); return rcur.execute("INSERT INTO users(tg_id,username) VALUES(?,?)",
                (tg_id, username or ""))
    c.commit()
    cur.execute("SELECT tg_id,username,coins,xp FROM users WHERE tg_id=?",(tg_id,))
    r=cur.fetchone(); c.close(); return rdef upd(tg_id, c_delta, x_delta):
    c=conn(); cur=c.cursor()
    cur.execute("UPDATE users SET coins=coins+?,xp=xp+? WHERE tg_id=?",
                (c_delta,x_delta,tg_id))
    c.commit(); c.close()bot=Bot(BOT_TOKEN)
dp=Dispatcher()

@dp.message(Command("start"))
async def start_cmd(m:types.Message):
    u=get_user(m.from_user.id,m.from_user.username)
    await m.reply(f"🔥 Miraplexity Marketplace\n"
                  f"Coins: {u[2]} | XP: {u[3]}\n"
                  "Use /profile or /spin")@dp.message(Command("profile"))
async def prof(m:types.Message):
    u=get_user(m.from_user.id,m.from_user.username)
    await m.reply(f"📜 Profile\n@{u[1]}\nCoins: {u[2]}\nXP: {u[3]}")SPINS=[
 ("Small win",5,2),
 ("Nice win",15,5),
 ("Big win",40,12),
 ("XP only",0,10),
 ("Miss",0,0)
]
COST=10@dp.message(Command("spin"))
async def spin(m:types.Message):
    u=get_user(m.from_user.id,m.from_user.username)
    if u[2]<COST:
        await m.reply(f"❌ Need {COST} coins.")
        return
    res=random.choice(SPINS)
    label,cg,xg=res
    upd(m.from_user.id,cg-COST,xg)u2=get_user(m.from_user.id,m.from_user.username)
    await m.reply(f"🎰 {label}\n"
                  f"Coin change: {cg-COST}\n"
                  f"XP gained: {xg}\n\n"
                  f"Now: {u2[2]} coins, {u2[3]} XP")async def main():
    init_db()
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
  
