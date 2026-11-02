
from aiogram.fsm.state import State, StatesGroup


class VideoSubmission(StatesGroup):
    waiting_for_video = State()
