from nonebot import message_preprocessor, on_command, on_notice, CommandSession, NoticeSession, NoneBot, SenderRoles
from nonebot.plugin import PluginManager
from nonebot.log import logger

import aiocqhttp
import aioredis
import config
import os


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
# wrong:用户ID - 插件用于记录错误次数，5分钟内超过2次则自动拉黑并通报
# group_member - 群员列表（集合）

__plugin_name__ = '注册验证'
__plugin_usage__ = '验证 [6位数字验证码]'


# 初始化redis连接池
r = aioredis.from_url("redis://localhost", decode_responses=True)

# 启动时：导入黑名单
try:
    with open('blacklist.csv') as f:
        blacklist = f.read().split(',')
        # 加await又说语法错误，不加又说未等待协同，Orz
        r.sadd('blacklist', blacklist)
        logger.info(f'成功导入redis黑名单备份，共{len(blacklist)}项')
except FileNotFoundError:
    logger.info('未找到redis黑名单备份')


# 备份黑名单
# 当群员变动，管理员手动备份或发送解封、封禁等指令时执行
# TODO: 想写成定时的但是搞不好。参考了见 https://docs.nonebot.dev/advanced/scheduler.html
async def backup():
    logger.info('备份redis黑名单成功')
    os.popen('redis-cli --csv SMEMBERS blacklist > blacklist.csv')


# 辅助逻辑：备份黑名单
@on_command('backup', aliases=('备份', '黑名单', '黑名单备份', '备份黑名单'), permission=lambda sender: sender.is_superuser)
async def on_backup(session: CommandSession):
    await backup()
    await session.send('备份redis黑名单成功')


# 消息预处理：检测黑名单
@message_preprocessor
async def _(bot: NoneBot, event: aiocqhttp.Event, plugin_manager: PluginManager):
    event["preprocessed"] = True
    if event.message_type == 'private' and await r.sismember('blacklist', str(event.user_id)):
        await bot.send_msg(user_id=event.user_id, message='禁止访问，请私聊空荧酒馆打点组管理员')
        logger.warn(f'用户{event.user_id}访问被拒绝')
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
            code = (await session.aget(prompt='验证码格式错误，请直接输入6位数字')).strip()
            continue
        break

    # redis无邀请码信息
    temp = await r.get(f'captcha:{session.event.user_id}')
    for i in range(1):
        # 已验证
        if await r.get(f'verified:{session.event.user_id}'):
            await session.send('已通过验证，请勿重复操作')
            return

        if not temp:
            await session.send('验证码不存在或超时，请重新注册')
            continue

        # redis验证码不匹配
        if temp != code:
            await session.send('验证码错误，请重新输入')
            continue

        break
    else:
        logger.warn(f'用户{session.event.user_id}输入了无效的验证码')
        if await r.get(f'wrong:{session.event.user_id}') is None:
            await r.setex(f'wrong:{session.event.user_id}', 300, 1)
            return

        await r.sadd('blacklist', session.event.user_id)
        await session.send('5分钟内输入2次无效验证码，自动拉黑，请联系空荧酒馆管理员处理')
        await session.bot.send_group_msg(group_id=992165223, message=f'用户{session.event.user_id}5分钟内输入2次无效验证码，自动拉黑')
        logger.warn(f'用户{session.event.user_id}5分钟内输入2次无效验证码，自动拉黑')
        return

    # 通过验证，修改redis键名
    await r.setex(f'verified:{session.event.user_id}', 300, 1)
    await r.delete(f'captcha:{session.event.user_id}')
    await session.send('已通过验证，请返回注册页，并在5分钟内点击注册')


# 辅助逻辑：手动更新群员名单
@on_command('flush', aliases=('获取群员', '更新群员', '刷新群员', '刷新', '更新', '获取'), permission=lambda sender: sender.is_superuser)
async def member_flush(session: CommandSession):
    ids = set()
    members = (await session.bot.get_group_member_list(group_id=config.GROUP_ID, self_id=config.BOT_ID))
    for u in members:
        ids.add(u['user_id'])

    logger.info(f'已刷新打点群员共{len(ids)}人')
    await r.delete('group_member')
    await r.sadd('group_member', *ids)
    await session.send(f'刷新成功，当前打点群员共{len(ids)}人')
    await backup()


# 辅助逻辑：新增群员，更新名单
@on_notice('increase')
async def member_increase(session: NoticeSession):
    logger.info(f'用户{session.event.user_id}入群，同步更新名单')
    await r.sadd('group_member', session.event.user_id)
    await backup()


# 辅助逻辑：删除群员，更新名单
@on_notice('decrease')
async def member_decrease(session: NoticeSession):
    logger.info(f'用户{session.event.user_id}退群，同步更新名单')
    await r.srem('group_member', session.event.user_id)
    await backup()


# 辅助逻辑：私聊拉黑
@on_command('ban', aliases=('拉黑', '封禁', '封号'), permission=lambda sender: sender.is_superuser)
async def member_ban(session: CommandSession):
    uid = session.current_arg_text.strip()
    while not uid.isdigit():
        uid = (await session.aget(prompt='请输入拉黑QQ号')).strip()

    await r.sadd('blacklist', uid)
    logger.info(f'拉黑用户{uid}')
    await session.send('拉黑成功')
    await backup()


# 辅助逻辑：私聊解封
@on_command('unban', aliases=('解封', '解禁'), permission=lambda sender: sender.is_superuser)
async def member_unban(session: CommandSession):
    uid = session.current_arg_text.strip()
    while not uid.isdigit():
        uid = (await session.aget(prompt='请输入解封QQ号')).strip()

    await r.srem('blacklist', uid)
    await r.delete(f'wrong:{uid}')
    logger.info(f'解封用户{uid}')
    await session.send('解封成功')
    await backup()


# 辅助逻辑：查询是否在黑名单
@on_command('in-blacklist', aliases=('查询黑名单', '黑名单查询'), permission=lambda sender: sender.is_superuser)
async def in_blacklist(session: CommandSession):
    uid = session.current_arg_text.strip()
    while not uid.isdigit():
        uid = (await session.aget(prompt='请输入查询QQ号')).strip()

    b = await r.sismember('blacklist', uid)
    await session.send(f'用户{uid}{"在" if b else "不在"}黑名单内')
