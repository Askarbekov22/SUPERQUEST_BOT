
from aiogram import Dispatcher

from bot.common.handlers import router as common_router

from bot.features.games.handlers import (
    router as games_router
)
from bot.features.contests.handlers import (
    router as contests_router
)
from bot.features.submissions.handlers import (
    router as submissions_router
)
from bot.features.winners.handlers import (
    router as winners_router
)
from bot.features.profile.handlers import (
    router as profile_router
)
from bot.features.community.handlers import (
    router as community_router
)


def setup_routers(dp: Dispatcher):
    dp.include_router(common_router)
    dp.include_router(games_router)
    dp.include_router(contests_router)
    dp.include_router(submissions_router)
    dp.include_router(winners_router)
    dp.include_router(profile_router)
    dp.include_router(community_router)
