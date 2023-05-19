from os import path

import nonebot
import config

# bot入口
if __name__ == '__main__':
    # 根据配置初始化
    nonebot.init(config)
    # 加载基础插件
    nonebot.load_builtin_plugins()
    # 加载所有插件
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'bot', 'plugins'),
        'bot.plugins'
    )
    nonebot.run()
