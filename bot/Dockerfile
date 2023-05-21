FROM python:3.9-alpine
MAINTAINER MomentDerek<1026821350@qq.com>
WORKDIR /usr/src/app
RUN pip install --no-cache-dir "nonebot" "aioredis"
COPY . .
CMD ["python", "bot.py"]