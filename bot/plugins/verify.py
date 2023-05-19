from nonebot import message_preprocessor, on_command, on_notice, CommandSession, NoticeSession, NoneBot, SenderRoles
from nonebot.plugin import PluginManager

import aiocqhttp
import redis
import config

# 注册验证插件
# @author  Icy（刻猫猫），icy_official@qq.com
# @author  MomentDerek 提出业务逻辑
# @company  Kongying Tavern 空荧酒馆
# 用法 Usage：私聊
# 验证 [6位数字验证码]

# 主业务逻辑
# 1. 用户在打点页填写注册表单后，点击发送验证码控件，访问后端api
# 2. 后端确认不在黑名单后，产生验证码写redis，并将结果回显
# 3. 用户通过QQ私发验证码，即通过本插件
# 4. 本插件通过验证，修改redis信息，并回显提示
# 5. 用户在打点页正式提交注册表单，访问后端api
# 6. 后端查redis，若有验证信息及时删除并完成注册，回显结果

# 辅助功能：
# 1. 监控群员列表，并通过redis保存，以供主业务逻辑中步骤2查询是否拥有注册权限
# 2. 对试图暴力验证的用户拉黑踢出并通报

# Redis键名规约
# captcha:用户ID - 主业务逻辑步骤2中后端所写，“待验证用户ID”
# verified:用户ID - 主业务逻辑步骤4中修改redis的键名，且需步骤6删除
# blacklist - 黑名单（集合），主业务逻辑2中后端查找，并可修改
# group_member - 群员列表（集合）

__plugin_name__ = '注册验证'
__plugin_usage__ = '验证 [6位数字验证码]'

# 初始化redis连接池
pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)


# 消息预处理：检测黑名单
@message_preprocessor
async def _(bot: NoneBot, event: aiocqhttp.Event, plugin_manager: PluginManager):
    event["preprocessed"] = True
    if event.message_type == 'private' and r.sismember('blacklist', str(event.user_id)):
        await bot.send_msg(user_id=event.user_id, message='禁止访问，请私聊空荧酒馆打点组管理员717818652')
        plugin_manager.switch_plugin("bot.plugins.verify", state=False)
        return
    plugin_manager.switch_plugin("bot.plugins.verify", state=True)


# 主业务逻辑：用户尝试校验验证码
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

    # redis无邀请码信息
    temp = r.get(f'captcha:{session.event.user_id}')
    if not temp:
        await session.send('验证码不存在或超时，请重新注册')
        return

    # redis验证码不匹配
    if temp != code:
        await session.send('验证码错误，请重新输入')
        return

    # 通过验证，修改redis键名
    r.setex(f'verified:{session.event.user_id}', 120, 1)
    r.delete(f'captcha:{session.event.user_id}')
    await session.send('已通过验证，请返回注册页，并在2分钟内点击注册')


# 辅助逻辑：手动更新群员名单
@on_command('flush', aliases=('获取群员', '更新群员', '刷新群员', '刷新', '更新', '获取'), permission=lambda sender: sender.is_superuser)
async def member_flush(session: CommandSession):
    ids = set()
    members = (await session.bot.get_group_member_list(group_id=config.GROUP_ID, self_id=config.BOT_ID))
    for u in members:
        ids.add(u['user_id'])

    r.sadd('group_member', *ids)
    await session.send(f'刷新成功，当前打点群员共{len(ids)}人')


# 辅助逻辑：新增群员，更新名单
@on_notice('increase')
async def member_increase(session: NoticeSession):
    r.sadd('group_member', session.event.user_id)


# 辅助逻辑：删除群员，更新名单
@on_notice('decrease')
async def member_decrease(session: NoticeSession):
    r.srem('group_member', session.event.user_id)


# 辅助逻辑：私聊拉黑
@on_command('ban', aliases=('拉黑', '封禁', '封号'), permission=lambda sender: sender.is_superuser)
async def member_ban(session: CommandSession):
    uid = session.current_arg_text.strip()
    while not uid.isdigit():
        uid = (await session.aget(prompt='请输入拉黑QQ号')).strip()

    r.sadd('blacklist', uid)
    await session.send('拉黑成功')


# 辅助逻辑：私聊解封
@on_command('unban', aliases=('解封', '解禁'), permission=lambda sender: sender.is_superuser)
async def member_unban(session: CommandSession):
    uid = session.current_arg_text.strip()
    while not uid.isdigit():
        uid = (await session.aget(prompt='请输入解封QQ号')).strip()

    r.srem('blacklist', uid)
    await session.send('解封成功')
