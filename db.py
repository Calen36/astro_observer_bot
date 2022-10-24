import asyncio
import sqlite3
import aiosqlite


def start_db():
    """Заново создает пустые таблицы базы данных"""
    db = sqlite3.connect('astro.db')
    db.execute('CREATE TABLE IF NOT EXISTS users(uid INTEGER PRIMARY KEY, lat TEXT, long TEXT, place TEXT, name TEXT, timezone TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS banlist(uid INTEGER PRIMARY KEY)')
    db.commit()


def sync_get_banned() -> list[str]:
    """Возвращает список забаненных userid"""
    with sqlite3.connect('astro.db') as connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT uid FROM banlist")
        rows = cursor.fetchall()
        cursor.close()
        return [x[0] for x in rows]


async def get_banlist() -> list[str]:
    """Возвращает список забаненных userid"""
    try:
        async with aiosqlite.connect('astro.db') as db:
            async with db.execute("SELECT * from banlist") as cursor:
                rows = await cursor.fetchall()
                return [x[0] for x in rows]
    except Exception as ex:
        print(ex)


async def get_banned_names() -> list[str]:
    """Возвращает список имен забаненных"""
    try:
        async with aiosqlite.connect('astro.db') as db:
            query = "SELECT banlist.uid, name FROM banlist LEFT JOIN users ON banlist.uid = users.uid;"
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [f"{x[0]} {x[1]}" for x in rows]
    except Exception as ex:
        print(ex)


async def ban_user(uid: int | str):
    """Добавляет userid в банлист"""
    try:
        async with aiosqlite.connect('astro.db') as db:
            await db.execute(f"INSERT INTO banlist VALUES('{uid}')")
            await db.commit()
    except Exception as ex:
        print(ex)


async def unban_user(uid: int | str):
    """Удаляет userid из банлиста"""
    try:
        async with aiosqlite.connect('astro.db') as db:
            await db.execute(f"DELETE FROM banlist WHERE uid = '{uid}'")
            await db.commit()
    except Exception as ex:
        print(ex)


async def get_users() -> tuple[int, str, str, str, str]:
    """Возвращает список  с информацией о пользователях"""
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            # rows = [x[0] for x in rows]
            return rows


async def get_user(uid: int | str):
    """Возвращает информацию о пользователе по userid"""
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT * FROM users WHERE uid = '{uid}'") as cursor:
            result = await cursor.fetchone()
            return result


async def update_user(uid: int | str, lat: str, long: str, place: str = '', name: str = '', timezone: str = ''):
    """Добавляет или обновляет информацию о пользователе"""
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT * FROM users WHERE uid = '{uid}'") as cursor:
            result = await cursor.fetchone()
        if result:
            await db.execute(f"UPDATE users SET lat = '{lat}', long = '{long}', place = '{place}', name = '{name}', timezone = '{timezone}' WHERE uid = {uid} ")
        else:
            await db.execute(f"INSERT INTO users VALUES ('{uid}', '{lat}', '{long}', '{place}', '{name}', '{timezone}')")
        await db.commit()


async def get_uid(username: str) -> int:
    """Возвращает userid пользователя по"""
    async with aiosqlite.connect('astro.db') as db:
        async with db.execute(f"SELECT uid FROM users WHERE name = '{username}'") as cursor:
            row = await cursor.fetchone()
            try:
                return row[0]
            except TypeError as ex:
                print(ex)
                return None


if __name__ == '__main__':
    start_db()
