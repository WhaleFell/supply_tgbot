# TG SUPPAY

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
