from nonebot import on_command, on_notice, CommandSession, NoticeSession
import redis
import config

pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)


@on_command('verify', aliases=('验证码', '注册', '验证'))
async def verify(session: CommandSession):
    code = session.current_arg_text.strip()
    while True:
        if not code:
            code = (await session.aget(prompt='请输入6位数字验证码')).strip()
            continue
        if not code.isdigit() or len(code) != 6:
            code = (await session.aget(prompt='验证码格式错误，请重新输入')).strip()
            continue
        break

    temp = r.get(f'captcha:{session.event.user_id}')
    if not temp:
        await session.send('验证码不存在或超时，请重新注册')
        return

    if temp != code:
        await session.send('验证码错误，请重新输入')
        return

    r.setex(f'verified:{session.event.user_id}', 120, 1)
    r.delete(f'captcha:{session.event.user_id}')
    await session.send('已通过验证，请返回注册页，并在2分钟内点击注册')


@on_command('flush', aliases=('获取群员', '更新群员', '刷新群员', '刷新', '更新', '获取'))
async def member_flush(session: CommandSession):
    if session.event.user_id not in config.SUPERUSERS:
        return

    ids = set()
    members = (await session.bot.get_group_member_list(group_id=config.GROUP_ID, self_id=config.BOT_ID))
    for u in members:
        ids.add(u['user_id'])

    r.sadd('group_member', *ids)
    await session.send(f'刷新成功，当前打点群员共{len(ids)}人')


@on_notice('increase')
async def member_increase(session: NoticeSession):
    r.sadd('group_member', session.event.user_id)


@on_notice('decrease')
async def member_decrease(session: NoticeSession):
    r.srem('group_member', session.event.user_id)
