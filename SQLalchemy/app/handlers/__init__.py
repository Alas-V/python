from aiogram import Dispatcher
from .hnd_processing import processing
from .hnd_user import user_router
from .hnd_support import support_router
from .hnd_review import review_router


def setup_router(dp: Dispatcher):
    dp.include_router(user_router)
    dp.include_router(processing)
    dp.include_router(support_router)
    dp.include_router(review_router)
