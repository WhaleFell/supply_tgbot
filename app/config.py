#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# config.py 配置文件

import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


# 应用路径
ROOTPATH: Path = Path().absolute().parent


# https://docs.pydantic.dev/usage/settings/
class Settings(BaseSettings):
    PROJECT_DESC: str = "🎉 接口汇总 🎉"  # 描述
    PROJECT_VERSION: str = "1.0"  # 版本

    # 末尾不能有 /
    EPUSDT_BACKEND: str = "http://192.168.8.1:8966"
    EPUSDT_CALLBACK_URL: str = "http://192.168.8.219:8000/pay/callback"
    EPUSDT_KEY: str = "lovehyy9420"

    # 跨域请求(务必指定精确ip, 不要用localhost)
    CORS_ORIGINS: Union[List[AnyHttpUrl], List[str]] = ["*"]

    # database config
    # SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
    # 异步 mysql+aiomysql://user:password@host:port/dbname
    # DB_URL = os.environ.get("DB_URL") or "mysql+aiomysql://root:123456@localhost/tgforward?charset=utf8mb4"
    DATABASE_URI: str = (
        "mysql+aiomysql://root:123456@localhost/tgsupply?charset=utf8mb4"
    )
    DATABASE_ECHO: bool = False  # 是否打印数据库日志 (可看到创建表、表数据增删改查的信息)

    # logger config
    LOGGER_SAVE: bool = False
    LOGGER_DIR: str = "logs"  # 日志文件夹名
    LOGGER_NAME: str = "{time:YYYY-MM-DD_HH-mm-ss}.log"  # 日志文件名 (时间格式)
    LOGGER_LEVEL: str = "DEBUG"  # 日志等级: ['DEBUG' | 'INFO']
    # 日志分片: 按 时间段/文件大小 切分日志. 例如 ["500 MB" | "12:00" | "1 week"]
    LOGGER_ROTATION: str = "00:00"
    LOGGER_RETENTION: str = "30 days"  # 日志保留的时间: 超出将删除最早的日志. 例如 ["1 days"]

    model_config = SettingsConfigDict(case_sensitive=True)  # 区分大小写


settings = Settings()
