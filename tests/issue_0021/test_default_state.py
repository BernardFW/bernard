from bernard.conf.utils import (
    patch_conf,
)
from bernard.engine.fsm import (
    FSM,
)
from bernard.utils import (
    run,
)

BASE_CONF = {'TRANSITIONS_MODULE': 'tests.issue_0021.transitions'}


async def get_fsm_problems():
    fsm = FSM()
    problems = []

    # noinspection PyTypeChecker
    async for problem in fsm.health_check():
        problems.append(problem)

    return problems


def test_default():
    with patch_conf(BASE_CONF):
        problems = run(get_fsm_problems())
    assert any(x.code == '00005' for x in problems)


def test_wrong_import():
    conf = dict(BASE_CONF)
    conf['DEFAULT_STATE'] = 'does.not.Exist'

    with patch_conf(conf):
        problems = run(get_fsm_problems())

    assert any(x.code == '00005' for x in problems)
