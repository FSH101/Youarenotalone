from aiogram.fsm.state import State, StatesGroup

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