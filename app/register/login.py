#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2023/1/31 10:05
# @Author : zxiaosi
# @desc : Fastapi-login 配置

from fastapi import FastAPI

# from fastapi_login import LoginManager
from app.config import settings
from app.database.curd import ConfigCurd
from app.database.connect import AsyncSessionMaker
import asyncio

from typing import Optional
from datetime import timedelta


# class NotAuthenticatedException(Exception):
#     pass


# manager = LoginManager(
#     settings.SECRET,
#     "/login",
#     use_cookie=True,
#     custom_exception=NotAuthenticatedException,
#     default_expiry=timedelta(hours=12),
# )


# @manager.user_loader()
# async def query_user(username="admin") -> Optional[dict]:
#     async with AsyncSessionMaker() as session:
#         config = await ConfigCurd.getConfig(session)
#         if not config:
#             return None
#         return {"username": "admin", "password": config.admin_password}
