# 空荧酒馆后厨QQ机器人
--------------------
![](https://img.shields.io/badge/python-3.11+-blue) [![](https://img.shields.io/pypi/v/nonebot2?label=nonebot)](https://pypi.python.org/pypi/nonebot2) [![](https://img.shields.io/github/v/release/Mrs4s/go-cqhttp?color=blueviolet&label=go-cqhttp)](https://github.com/Mrs4s/go-cqhttp/releases) [![](https://img.shields.io/badge/OneBot-v11-black?style=social&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABABAMAAABYR2ztAAAAIVBMVEUAAAAAAAADAwMHBwceHh4UFBQNDQ0ZGRkoKCgvLy8iIiLWSdWYAAAAAXRSTlMAQObYZgAAAQVJREFUSMftlM0RgjAQhV+0ATYK6i1Xb+iMd0qgBEqgBEuwBOxU2QDKsjvojQPvkJ/ZL5sXkgWrFirK4MibYUdE3OR2nEpuKz1/q8CdNxNQgthZCXYVLjyoDQftaKuniHHWRnPh2GCUetR2/9HsMAXyUT4/3UHwtQT2AggSCGKeSAsFnxBIOuAggdh3AKTL7pDuCyABcMb0aQP7aM4AnAbc/wHwA5D2wDHTTe56gIIOUA/4YYV2e1sg713PXdZJAuncdZMAGkAukU9OAn40O849+0ornPwT93rphWF0mgAbauUrEOthlX8Zu7P5A6kZyKCJy75hhw1Mgr9RAUvX7A3csGqZegEdniCx30c3agAAAABJRU5ErkJggg==)](https://github.com/botuniverse/onebot-11)

## 项目需求
 - [需求看板连接](https://github.com/orgs/kongying-tavern/projects/6?pane=issue&itemId=25786978)

## 启动

### 本地开发
  - 机器人 `python` 开发环境配置
    ``` shell
      # in ./bot 目录
      pip -m venv .venv
      pip install nb-cli
      pip install redis

      # 安装nonebot依赖
      nb driver install nonebot2[fastapi]
      nb driver install nonebot2[httpx]
      nb driver install nonebot2[websockets]
      nb adapter install nonebot-adapter-onebot
    ```
  - 机器人 `env` 配置
    ``` conf
      # 注意除非配置.env文件 否则 nb-cli 默认选择
      # .env.prod作为项目环境

      # 默认驱动器
      DRIVER = ~fastapi+~httpx+~websockets
      # 日志等级
      LOG_LEVEL = DEBUG
      # 管理员列表，值必须为json可解析的字符串数组 string[]
      SUPERUSERS = []
      # 命令起始符 string[]
      COMMAND_START = []
      # 群号
      GROUP_ID = ""
      # 机器人账号
      BOT_ID = ""
      # 服务开启的主机与端口，必须如下配置
      HOST = "0.0.0.0"
      PORT = "8080"
    ```
  - `go-cqhttp` 本地启动，[教程参考](https://docs.go-cqhttp.org/guide/quick_start.html#%E5%9F%BA%E7%A1%80%E6%95%99%E7%A8%8B)
    > 注意：
    > 1. 使用自动生成的 `device.json` 文件
    > 2. config.yml 必须使用账户密码登录
    > 3. 反向ws地址必须为 `ws://127.0.0.1/onebot/v11/ws`
    > 4. 下载好的 go-cqhttp 另起一个工作目录，它配置与本项目并不完全相同
  - 在 `./bot` 目录下执行 `nb run` 命令

### 项目部署
  - `nonebot` 配置部分与本地开发相同
  - `./gocqhttp` 的 `config.yaml` 必须配置账户密码，项目启动时切勿挂代理，容易造成账号风控。
  - 反向 `ws` 地址必须为 `ws://register-bot:8080/onebot/v11/ws`