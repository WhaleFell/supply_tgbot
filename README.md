# TG 供需机器人

包含供需机器人的前后端,时间紧任务重,得赶快了！！！！！

这是 1100 的订单啊！！！！熬夜也要完成，胜败在此一举！！！

## 需要搭建 USDT 支付回调

[https://github.com/assimon/epusdt](https://github.com/assimon/epusdt)

## 部署

```shell
docker build -t tgbot -f ./DockerfileTGBot .
docker build -t fastapi -f ./DockerfileFastAPI .
docker-compose up -d
```

## Docker-compose.yaml

```yaml
version: "3"
services:
  db:
    image: mariadb:focal
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=lovehyy
      - MYSQL_DATABASE=epusdt
      - MYSQL_USER=epusdt
      - MYSQL_PASSWORD=lovehyy
    volumes:
      - ./mysql:/var/lib/mysql

  redis:
    image: redis:alpine
    restart: always
    volumes:
      - ./redis:/data

  epusdt:
    image: stilleshan/epusdt
    restart: always
    volumes:
      - ./epusdt.conf:/app/.env
    ports:
      - 8000:8000
```

## New Requirements 新需求

1. 支付成功、超时提醒 -> 开一个 coroutine 遍历数据库 pays 表，添加一个 notice:bool 字段
2. 选择供给还是需求时改用回复，机器人监听回复信息，并验证是否含有相关字段
3. 个人中心按钮添加最近的成功充值记录，并去除用户 ID
4. 发布成功后返回频道链接 -> msg 表添加一个字段 url.
5. 添加一个发布记录按钮，查看最近的发布记录和消耗的金额
6. 支持发布多个频道,后台设置频道 -> 修改 config 表的 channel_id 字段
