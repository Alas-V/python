from aiogram import Dispatcher
from .hnd_processing import processing
from .hnd_user import user_router
from .hnd_support import support


def setup_router(dp: Dispatcher):
    dp.include_router(user_router)
    dp.include_router(processing)
    dp.include_router(support)
