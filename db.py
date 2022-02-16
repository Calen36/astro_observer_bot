import sqlite3
import aiosqlite


def start_db():
    base = sqlite3.connect('astro.db')
    base.execute('CREATE TABLE IF NOT EXISTS users(uid INTEGER PRIMARY KEY, lat TEXT, long TEXT, name TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS banlist(uid INTEGER PRIMARY KEY)')
    base.commit()

# start_db()


async def get_banned():
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT uid FROM banlist") as cursor:
            rows = await cursor.fetchall()
            rows = [x[0] for x in rows]
            return rows


async def get_users():
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT uid FROM users") as cursor:
            rows = await cursor.fetchall()
            rows = [x[0] for x in rows]
            return rows


async def get_user(uid):
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT * FROM users WHERE uid = '{uid}'") as cursor:
            result = await cursor.fetchone()
            return result


async def update_user(uid, lat, long, name=''):
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT * FROM users WHERE uid = '{uid}'") as cursor:
            result = await cursor.fetchone()
        if result:
            await db.execute(f"UPDATE users SET lat = '{lat}', long = '{long}', name = '{name}' WHERE uid = {uid} ")
        else:
            await db.execute(f"INSERT INTO users VALUES ('{uid}', '{lat}', '{long}', '{name}')")
        await db.commit()
