from aiogram import Dispatcher
from .user import user_router


def setup_router(dp: Dispatcher):
    dp.include_router(user_router)
