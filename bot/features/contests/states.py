
from aiogram.fsm.state import State, StatesGroup


class NewContest(StatesGroup):
    game = State()
    title = State()
    task = State()
    criteria = State()
    prize = State()
    start = State()
    end = State()
    confirm = State()
