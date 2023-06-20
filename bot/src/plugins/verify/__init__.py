from nonebot import get_driver, MatcherGroup, on_message
from nonebot.typing import T_State
from nonebot.plugin import on_command, PluginManager, on_notice
from nonebot.log import logger
from nonebot.message import event_preprocessor
from nonebot.permission import SUPERUSER
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText
from nonebot.adapters.onebot.v11.bot import Bot as BOT
from nonebot.adapters.onebot.v11.event import Event as EVENT
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, GroupMessageEvent, MessageSegment, NoticeEvent
import redis
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

config = get_driver().config
driver = get_driver()

# 初始化redis连接池
r = redis.Redis(host='redis', port=6379, decode_responses=True)

try:
  response = r.client_list()
  logger.success('redis 连接成功')
except redis.ConnectionError:
  logger.error('redis 连接失败')
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
backup_command = on_command('backup', aliases={'备份', '黑名单', '黑名单备份', '备份黑名单'}, permission=SUPERUSER)
# @on_command('backup', aliases=('备份', '黑名单', '黑名单备份', '备份黑名单'), permission=lambda EventParam:)
@backup_command.handle()
async def on_backup():
  await backup()
  await backup_command.finish('备份redis黑名单成功')


# 消息预处理：检测黑名单
async def auth_check(bot: BOT, event: PrivateMessageEvent, state: T_State) -> bool:
  if await r.sismember('blacklist', str(event.get_user_id())):
    await bot.send_msg(user_id=event.get_user_id(), message='禁止访问，请私聊空荧酒馆打点组管理员',message_type='private')
    logger.warning(f'用户{event.get_user_id()}访问被拒绝')
    return False
  return True

# 受黑名单权限控制的事件处理组
permit = MatcherGroup(rule=auth_check)

# 主业务逻辑：用户尝试校验验证码
verify = permit.on_command('verify', aliases={'验证码', '注册', '验证'})
@verify.handle()
async def on_verify( matcher: Matcher, state: T_State, args: Message = CommandArg()):
  if args.extract_plain_text():
    matcher.set_arg('code', args)

@verify.got("code", prompt='请输入6位数字验证码')
async def verify_code(bot: BOT, event:PrivateMessageEvent, code:str = ArgPlainText()):

  async def on_warn():
    logger.warn(f'用户{event.get_user_id()}输入了无效的验证码')
    failed_times = r.get(f'wrong:{event.get_user_id()}')
    if failed_times is None:
      r.setex(f'wrong:{event.get_user_id()}', 300, 1)

    if failed_times == 2:
      logger.warn(f'用户{event.get_user_id()}5分钟内输入2次无效验证码，自动拉黑')
      await bot.send_msg(message_type='group', group_id=config.group_id, message=f'用户{event.get_user_id()}5分钟内输入2次无效验证码，自动拉黑')
      r.sadd('blacklist', event.get_user_id())
      await verify.finish('5分钟内输入2次无效验证码，自动拉黑，请联系空荧酒馆管理员处理')

    if failed_times == 1:
      await r.setex(f'wrong:{event.get_user_id()}', 300, 2)



  if not code.isdigit() or len(code) != 6:
    await verify.reject('验证码格式错误，请直接输入6位数字')
    # redis无邀请码信息
  temp = await r.get(f'captcha:{event.get_user_id()}')
  if await r.get(f'verified:{event.get_user_id()}'):
    await verify.finish('已通过验证，请勿重复操作')

  if not temp:
    await on_warn()
    await verify.reject('验证码不存在或超时，请重新注册')

  # redis验证码不匹配
  if temp != code:
    await on_warn()
    await verify.reject('验证码错误，请重新输入')

  # 通过验证，修改redis键名
  await r.setex(f'verified:{event.get_user_id()}', 300, 1)
  await r.delete(f'captcha:{event.get_user_id()}')
  await verify.finish('已通过验证，请返回注册页，并在5分钟内点击注册')

# 辅助逻辑：手动更新群员名单
flush = permit.on_command(cmd='flush', priority=1, aliases={'获取群员', '更新群员', '刷新群员', '刷新', '更新', '获取'}, permission=SUPERUSER)
@flush.handle()
async def member_flush(bot: BOT):
  ids = set()
  members = (await bot.get_group_member_list(group_id=config.group_id))
  for u in members:
      ids.add(u['user_id'])

  logger.info(f'已刷新打点群员共{len(ids)}人')
  r.delete('group_member')
  r.sadd('group_member', *ids)

  await backup()
  await flush.finish(f'刷新成功，当前打点群员共{len(ids)}人')

async def leave_rule(bot: BOT, event: NoticeEvent, state: T_State) -> bool:
  if event.notice_type == 'group_decrease':
    return True
  return False

async def approve_rule(bot: BOT, event: NoticeEvent, state: T_State) -> bool:
  if event.notice_type == 'group_increase':
    return True
  return False

# 辅助逻辑：新增群员，更新名单
increase = on_notice(approve_rule)
@increase.handle()
async def member_increase(event: NoticeEvent):
    logger.info(f'用户{event.get_user_id()}入群，同步更新名单')
    r.sadd('group_member', event.get_user_id())
    await backup()


# 辅助逻辑：删除群员，更新名单
decrease = on_notice(leave_rule)
@decrease.handle()
async def member_decrease(event: NoticeEvent):
    logger.info(f'用户{event.get_user_id()}退群，同步更新名单')
    r.srem('group_member', event.get_user_id())
    await backup()


# 辅助逻辑：私聊拉黑
ban = on_command('ban', aliases={'拉黑', '封禁', '封号'}, permission=SUPERUSER)
@ban.handle()
async def member_ban( matcher: Matcher, state: T_State, args: Message = CommandArg()):
  if args.extract_plain_text():
    matcher.set_arg('ban_user', args)

@ban.got('ban_user', prompt='请输入拉黑QQ号')
async def on_ban(ban_user: str = ArgPlainText()):
  if not ban_user.isdigit():
    ban.reject('QQ号格式错误，请重试')

  r.sadd('blacklist', ban_user)
  logger.info(f'拉黑用户{ban_user}')

  await backup()
  await ban.finish('拉黑成功')


# 辅助逻辑：私聊解封
unban = on_command('unban', aliases={'解封', '解禁'}, permission=SUPERUSER)
@unban.handle()
async def member_unban( matcher: Matcher, state: T_State, args: Message = CommandArg()):
  if args.extract_plain_text():
    matcher.set_arg('unban_user', args)

@unban.got('unban_user', prompt='请输入解封QQ号')
async def on_unban(unban_user: str = ArgPlainText()):
  if not unban_user.isdigit():
    unban.reject('QQ号格式错误，请重试')

  r.srem('blacklist', unban_user)
  r.delete(f'wrong:{unban_user}')
  logger.info(f'解封用户{unban_user}')

  await backup()
  await unban.finish('拉黑成功')


# 辅助逻辑：查询是否在黑名单
blacklist = on_command('in-blacklist', aliases={'查询黑名单', '黑名单查询'}, permission=SUPERUSER)
@blacklist.handle()
async def member_unban( matcher: Matcher, state: T_State, args: Message = CommandArg()):
  if args.extract_plain_text():
    matcher.set_arg('user', args)

@blacklist.got('user', prompt='请输入解封QQ号')
async def on_unban(user: str = ArgPlainText()):
  if not user.isdigit():
    blacklist.reject('QQ号格式错误，请重试')

  b = r.sismember('blacklist', user)
  await blacklist.finish(f'用户{user}{"在" if b else "不在"}黑名单内')

