## 食用方法
### 启动方法
* 确保本机已开启`redis`，并置默认端口与空密码
* `cd`进入`go-cqhttp`目录下！！！后执行`go-cqhttp`
* 返回根目录终端执行`python bot.py`
### 首次运行？
* 使用`pip install`安装依赖`nonebot`和`redis`
* 根据系统解压对应的`go-cqhttp`压缩包
* `cd`进入`go-cqhttp`目录下！！！后执行`go-cqhttp`，按提示操作进行初始化配置
* 记得配置`go-http`的`config.yaml`！！主要是第`4`、`5`、`101`行
### 结构说明
* 启动入口在`bot.py`
* `bot`包下为相关代码，主要在其中`plugins`包下，为实现主要功能的插件
* `go-cqhttp`中存放启动所需资源，未使用版本控制