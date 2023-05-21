# 食用方法
## 结构说明
* `bot`目录下为主程序体（后端）
* `go-cqhttp`中存放启动所需资源（QQ）
* 启动入口在`bot.py`
* 主要功能插件在`plugins`包下
## 调~~戏~~试方法
### 首次调试？
* 使用`pip install`安装依赖`nonebot`，`aioredis`
* 根据系统解压对应的`go-cqhttp`压缩包
* `cd`进入`gocqhttp`目录下！！！后执行`go-cqhttp`，按提示操作进行初始化配置
* 记得配置`gohttp`的`config.yaml`！！主要是第`4`、`5`、`101`行
* PyCharm编辑配置，脚本路径到`\bot\bot.py`，工作目录到`\bot`
### 调试方法
* 确保本机已开启`redis`，并置默认端口与空密码
* `cd`进入`gocqhttp`目录下！！！后执行`go-cqhttp`
* 返回根目录终端执行`python bot.py`
## 部署方法
TBA.