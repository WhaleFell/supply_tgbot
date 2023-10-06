#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# register/router.py 注册路由
import secrets
from fastapi import FastAPI, Depends, status, APIRouter
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from typing_extensions import Annotated

from app.config import settings
from app.routers import index, pay_callback, set_config, user
from app.database.connect import AsyncSessionMaker
from app.database.curd import ConfigCurd

# 基本身份验证
# Docs: https://fastapi.tiangolo.com/advanced/security/http-basic-auth/
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic()
logout = APIRouter()


async def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    # basic http auth
    async with AsyncSessionMaker() as session:
        config = await ConfigCurd.getConfig(session)

    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"admin"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = config.admin_password.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@logout.get("/logout")
async def logout_basic_auth():
    # basic http auth logout
    # https://stackoverflow.com/questions/233507/how-to-log-out-user-from-web-site-using-basic-authentication/233551#233551
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Basic"},
    )


def register_router(app: FastAPI):
    """注册路由"""

    # app.include_router(
    #     public.router, prefix=settings.API_PREFIX, tags=["Public"]
    # )

    app.include_router(
        index.router,
        tags=["index"],
        dependencies=[Depends(get_current_username)],
    )
    # app.include_router(user.router, tags=["user"], prefix="/user")
    app.include_router(logout, tags=["logout"])
    app.include_router(pay_callback.router, tags=["pay"], prefix="/pay")
    app.include_router(set_config.router, tags=["config"], prefix="/config")
    app.include_router(user.router, tags=["user"], prefix="/user")
