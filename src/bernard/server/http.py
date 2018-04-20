# coding: utf-8
from aiohttp.web import (
    Application,
)
from aiohttp.web_urldispatcher import (
    UrlDispatcher,
)

from bernard.platforms.facebook import (
    web as fb,
)

from .views import (
    health_check,
    postback_analytics,
    postback_me,
    postback_send,
)

app = Application()

router = app.router  # type: UrlDispatcher

router.add_get('/health_check', health_check)
router.add_get('/hooks/facebook', fb.check_hook)
router.add_post('/hooks/facebook', fb.receive_events)
router.add_get('/postback/me', postback_me)
router.add_post('/postback/send', postback_send)
router.add_post('/postback/analytics', postback_analytics)
