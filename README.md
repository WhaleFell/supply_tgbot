# TG 供需机器人

包含供需机器人的前后端,时间紧任务重,得赶快了！！！！！

这是 1100 的订单啊！！！！熬夜也要完成，胜败在此一举！！！

## 需要搭建 USDT 支付回调

[https://github.com/assimon/epusdt](https://github.com/assimon/epusdt)

## 部署

```shell
docker build -t tgbot DockerfileTGBot
docker build -t fastapi DockerfileFastAPI
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
