
import aiosqlite

DB_PATH = "thoughts.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Удаляем старые таблицы и создаем новые с правильной структурой
        await db.execute("DROP TABLE IF EXISTS thoughts;")
        await db.execute("DROP TABLE IF EXISTS supports;")
        
        await db.execute("""
            CREATE TABLE thoughts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                topic TEXT,
                reply_to INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.execute("""
            CREATE TABLE supports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thought_id INTEGER NOT NULL,
                supporter_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (thought_id) REFERENCES thoughts (id)
            );
        """)
        await db.commit()

async def save_thought(user_id, text, topic=None, reply_to=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO thoughts (user_id, text, topic, reply_to) VALUES (?, ?, ?, ?);", (user_id, text, topic, reply_to))
        await db.commit()

# db.py
async def get_random_thought(exclude_user_id=None):
    if exclude_user_id:
        query = """
        SELECT id, text FROM thoughts
        WHERE user_id != $1
        ORDER BY RANDOM()
        LIMIT 1
        """
        row = await db.fetchrow(query, exclude_user_id)
    else:
        query = """
        SELECT id, text FROM thoughts
        ORDER BY RANDOM()
        LIMIT 1
        """
        row = await db.fetchrow(query)

    if row:
        return row["id"], row["text"]
    return None
    
async def get_thought_author(thought_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM thoughts WHERE id = ?;", (thought_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_support(thought_id, supporter_id, text):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO supports (thought_id, supporter_id, text) VALUES (?, ?, ?)",
            (thought_id, supporter_id, text)
        )
        await db.commit()

async def count_supports(thought_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM supports WHERE thought_id = ?",
            (thought_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_user_thoughts(user_id, sort_by="date_desc"):
    query = "SELECT id, text, topic, created_at FROM thoughts WHERE user_id = ?"
    if sort_by == "date_asc":
        query += " ORDER BY created_at ASC"
    elif sort_by == "topic":
        query += " ORDER BY topic ASC, created_at DESC"
    else:
        query += " ORDER BY created_at DESC"

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query, (user_id,)) as cursor:
            return await cursor.fetchall()

async def delete_thought(user_id, thought_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM thoughts WHERE id = ? AND user_id = ?", (thought_id, user_id))
        await db.commit()

async def get_support_replies(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT s.text
            FROM thoughts t
            JOIN supports s ON s.thought_id = t.id
            WHERE t.user_id = ?
            ORDER BY s.created_at DESC
        """, (user_id,)) as cursor:
            return [row[0] async for row in cursor]

# Получить случайную чужую мысль по теме
async def get_random_thought_by_topic(topic, user_id):
    async with aiosqlite.connect("thoughts.db") as db:
        async with db.execute("""
            SELECT text FROM thoughts 
            WHERE topic = ? AND user_id != ? 
            ORDER BY RANDOM() LIMIT 1
        """, (topic, user_id)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None
