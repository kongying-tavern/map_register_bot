# FROM python:3.9-alpine
# MAINTAINER MomentDerek<1026821350@qq.com>
# WORKDIR /usr/src/app
# COPY . .
# RUN pip install -r requirements.txt
# CMD ["python", "bot.py"]

FROM python:3.11-slim-buster

WORKDIR /usr/src

COPY . .

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
  && pip install nb-cli \
  && nb driver install nonebot2[fastapi] \
  && nb driver install nonebot2[httpx] \
  && nb driver install nonebot2[websockets] \
  && nb adapter install nonebot-adapter-onebot \
  && pip install redis

EXPOSE 8080

CMD ["nb", "run"]