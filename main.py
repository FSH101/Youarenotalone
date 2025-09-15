
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import os
import db

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# === FSM состояния ===
class Form(StatesGroup):
    choosing_topic = State()
    writing_thought = State()
    writing_support = State()

class ManageThoughts(StatesGroup):
    choosing_sort = State()
    choosing_delete = State()

class ListenThoughts(StatesGroup):
    choosing_topic = State()
    showing_thought = State()

# User data storage
user_data = {}

# === Главное меню ===
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Поговорить")],
            [KeyboardButton(text="🎧 Слушать мысли")],
            [KeyboardButton(text="🗂 Мои мысли")],
            [KeyboardButton(text="💬 Что мне сказали")]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def start(message):
    await message.answer(
        "👋 Привет. Это бот *Ты не один*.\nЗдесь ты можешь делиться мыслями и читать чужие — абсолютно анонимно.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "📝 Поговорить")
async def button_talk(message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💔 Любовь"), KeyboardButton(text="🌫 Потеря")],
            [KeyboardButton(text="😔 Одиночество"), KeyboardButton(text="🌱 Надежда")],
            [KeyboardButton(text="🌪 Тревога"), KeyboardButton(text="🕳 Депрессия")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(Form.choosing_topic)
    await message.answer("О чём ты хочешь поговорить?", reply_markup=keyboard)

@dp.message(Form.choosing_topic)
async def choose_topic(message, state: FSMContext):
    await state.update_data(topic=message.text)
    await message.answer("✍️ Напиши свою мысль:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏠 Главное меню")]], resize_keyboard=True))
    await state.set_state(Form.writing_thought)

@dp.message(Form.writing_thought)
async def handle_thought(message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.clear()
        await message.answer("Главное меню", reply_markup=main_menu())
        return
    
    data = await state.get_data()
    topic = data.get("topic")
    
    await db.save_thought(message.from_user.id, message.text, topic)
    result = await db.get_random_thought()
    if result:
        thought_id, thought_text = result
        await state.update_data(current_thought_id=thought_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❤️ Поддержать", callback_data=f"support_{thought_id}")]
        ])
        await message.answer(f"🫂 Мысль другого человека:\n\n\"{thought_text}\"", reply_markup=keyboard)
    else:
        await message.answer("Пока мыслей нет. Ты стал первым 💬", reply_markup=main_menu())
    await state.clear()

@dp.message(F.text == "🎧 Слушать мысли")
async def start_listen(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💔 Любовь"), KeyboardButton(text="🌫 Потеря")],
            [KeyboardButton(text="😔 Одиночество"), KeyboardButton(text="🌱 Надежда")],
            [KeyboardButton(text="🌪 Тревога"), KeyboardButton(text="🕳 Депрессия")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери тему, чтобы услышать чужие мысли:", reply_markup=keyboard)
    await state.set_state(ListenThoughts.choosing_topic)

    @dp.message(ListenThoughts.choosing_topic)
    async def show_thought_by_topic(message: types.Message, state: FSMContext):
        if message.text == "🔙 Назад":
            await message.answer("Главное меню", reply_markup=main_menu())
            await state.clear()
            return

        topic = message.text
        await state.update_data(topic=topic)

        result = await db.get_random_thought_by_topic(topic, message.from_user.id)  # теперь возвращает (id, text)

        if not result:
            await message.answer("😔 Пока нет мыслей по этой теме от других.", reply_markup=main_menu())
            await state.clear()
            return

        thought_id, thought_text = result
        await state.update_data(current_thought_id=thought_id)

        # Создаем inline кнопку поддержки
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❤️ Поддержать", callback_data=f"support_{thought_id}")]
        ])

        # Кнопки навигации
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🎲 Следующая"), KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True
        )

        # Отправляем мысль с inline кнопкой
        await message.answer(f"🧠 {thought_text}", reply_markup=inline_kb)
        # Отдельно отправляем кнопки навигации
        await message.answer("🔁 Можешь посмотреть следующую мысль или вернуться назад:", reply_markup=kb)

        await state.set_state(ListenThoughts.showing_thought)

        @dp.message(ListenThoughts.showing_thought)
        async def next_or_back(message: types.Message, state: FSMContext):
            if message.text == "🔙 Назад":
                await message.answer("Главное меню", reply_markup=main_menu())
                await state.clear()
                return

            if message.text == "🎲 Следующая":
                data = await state.get_data()
                topic = data.get("topic")

                result = await db.get_random_thought_by_topic(topic, message.from_user.id)
                if not result:
                    await message.answer("Больше мыслей по этой теме пока нет.")
                    return

                thought_id, thought_text = result
                await state.update_data(current_thought_id=thought_id)

                inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❤️ Поддержать", callback_data=f"support_{thought_id}")]
                ])

                await message.answer(f"🧠 {thought_text}", reply_markup=inline_kb)
        
@dp.message(F.text == "🗂 Мои мысли")
async def choose_sorting(message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🕓 По дате"), KeyboardButton(text="🔠 По теме")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Как отсортировать твои мысли?", reply_markup=keyboard)
    await state.set_state(ManageThoughts.choosing_sort)

@dp.message(ManageThoughts.choosing_sort)
async def show_thoughts(message, state: FSMContext):
    if message.text == "🔙 Назад":
        await message.answer("Главное меню", reply_markup=main_menu())
        await state.clear()
        return

    sort = "date_desc"
    if message.text == "🕓 По дате":
        sort = "date_desc"
    elif message.text == "🔠 По теме":
        sort = "topic"

    thoughts = await db.get_user_thoughts(message.from_user.id, sort)
    if not thoughts:
        await message.answer("😶 Ты пока ничего не писал.", reply_markup=main_menu())
        await state.clear()
        return

    # Создаем клавиатуру с мыслями для удаления
    buttons = []
    for t in thoughts[:10]:  # ограничим 10 мыслей
        short = (t[1][:40] + "...") if len(t[1]) > 40 else t[1]
        topic_emoji = t[2] if t[2] else "💭"
        buttons.append([KeyboardButton(text=f"🗑 Удалить {t[0]} — {topic_emoji} {short}")])
    
    buttons.append([KeyboardButton(text="🔙 Назад")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    reply = "🧾 Вот твои мысли:\n\n"
    for i, t in enumerate(thoughts[:10], 1):
        topic_text = f" [{t[2]}]" if t[2] else ""
        reply += f"{i}.{topic_text} {t[1][:100]}{'...' if len(t[1]) > 100 else ''}\n\n"
    
    reply += "Можешь удалить любую:"

    await state.update_data(thoughts=thoughts)
    await message.answer(reply, reply_markup=keyboard)
    await state.set_state(ManageThoughts.choosing_delete)

@dp.message(ManageThoughts.choosing_delete)
async def delete_selected(message, state: FSMContext):
    if message.text == "🔙 Назад":
        await message.answer("Главное меню", reply_markup=main_menu())
        await state.clear()
        return

    if message.text.startswith("🗑 Удалить "):
        try:
            # Извлекаем ID из текста кнопки
            parts = message.text.split()
            thought_id = int(parts[2])
            await db.delete_thought(message.from_user.id, thought_id)
            await message.answer("✅ Мысль удалена", reply_markup=main_menu())
            await state.clear()
            return
        except (ValueError, IndexError):
            await message.answer("❌ Ошибка при удалении.", reply_markup=main_menu())
            await state.clear()
            return
    else:
        await message.answer("Пожалуйста, выбери мысль для удаления или нажми 'Назад'.")

@dp.message(F.text == "💬 Что мне сказали")
async def show_support_replies(message):
    replies = await db.get_support_replies(message.from_user.id)
    if not replies:
        await message.answer("😶 Ты ещё не получил ответов.", reply_markup=main_menu())
    else:
        reply = "🗣 Вот что тебе сказали:\n\n"
        for i, r in enumerate(replies[:10], 1):
            reply += f"{i}. {r[:100]}{'...' if len(r) > 100 else ''}\n\n"
        await message.answer(reply, reply_markup=main_menu())

@dp.callback_query(F.data.startswith("support_"))
async def support_thought(callback, state: FSMContext):
    thought_id = int(callback.data.split("_")[1])
    await state.update_data(current_thought_id=thought_id)
    await state.set_state(Form.writing_support)
    await bot.send_message(callback.from_user.id, "💌 Напиши слова поддержки. Я передам автору мысли.")
    await callback.answer()

@dp.message(Form.writing_support)
async def receive_support(message, state: FSMContext):
    data = await state.get_data()
    thought_id = data.get("current_thought_id")
    author_id = await db.get_thought_author(thought_id)

    # Сохраняем поддержку
    await db.save_support(thought_id, message.from_user.id, message.text)

    # Подсчитываем общее количество поддержек
    support_count = await db.count_supports(thought_id)

    if author_id:
        try:
            await bot.send_message(
                author_id,
                f"🌟 Кто-то поддержал твою мысль:\n\n\"{message.text}\""
            )
            if support_count in [3, 5, 10]:  # можно расширить список порогов
                await bot.send_message(
                    author_id,
                    f"🧡 Твою мысль уже поддержали {support_count} раз(а).\nТы точно не один."
                )
        except:
            pass

    await message.answer("✅ Поддержка отправлена!", reply_markup=main_menu())
    await state.clear()

@dp.message()
async def fallback(message):
    await message.answer(
        "🤔 Я тебя не понял. Нажми на одну из кнопок ниже:",
        reply_markup=main_menu()
    )

async def main():
    await db.init_db()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
