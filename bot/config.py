from nonebot.default_config import *
# 生产模式置False以提高性能
DEBUG = True

# 管理员的号
SUPERUSERS = {1404647441, 1026821350, 717818652, 1809521264}
COMMAND_START = {'#'}

# 这里填打点群号
GROUP_ID = 992165223

# 这里填bot的QQ号，记得同步更新go-cqhttp中config.yaml配置3、4行
BOT_ID = 1508371405

# 注意：修改HOST与PORT，需要更新go-cqhttp中config.yaml配置101行
HOST = '127.0.0.1'
PORT = '8080'
