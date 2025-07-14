from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

import db
from states import Form
from keyboards.main_menu import get_main_menu

router = Router()

@router.message(F.text == "📝 Поговорить")
async def button_talk(message: types.Message, state: FSMContext):
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

@router.message(Form.choosing_topic)
async def choose_topic(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
        resize_keyboard=True
    )
    await state.set_state(Form.writing_thought)
    await message.answer("✍️ Напиши свою мысль:", reply_markup=keyboard)

@router.message(Form.writing_thought)
async def handle_thought(message: types.Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_main_menu())
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
        await message.answer("Пока мыслей нет. Ты стал первым 💬", reply_markup=get_main_menu())

    await state.clear()