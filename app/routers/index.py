#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# index router 登录路由

# Docs: https://fastapi-login.readthedocs.io/usage/

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import RedirectResponse, ORJSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException

from typing_extensions import Annotated
from typing import Optional
from app.schemas import BaseResp
from pathlib import Path

from app.config import settings

# from app.register.login import manager, query_user
from fastapi_login.exceptions import InvalidCredentialsException

router = APIRouter()


# @router.route("/login/", methods=["GET", "POST"])
# async def login(
#     response: Response,
#     data: Annotated[Optional[OAuth2PasswordRequestForm], Depends()] = None,
# ):
#     if not data:
#         return ORJSONResponse(content={"index": "swsw"})
#     username = data.username
#     password = data.password

#     user = await query_user(username="admin")
#     if not user:
#         raise InvalidCredentialsException
#     if username != user["username"]:
#         raise InvalidCredentialsException
#     elif password != user["password"]:
#         raise InvalidCredentialsException

#     token = manager.create_access_token(data={"sub": username})

#     manager.set_cookie(response, token)
#     return BaseResp(code=200, msg="登录成功")


# @router.get("/logout")
# async def logout():
#     # basic http auth logout
#     # https://stackoverflow.com/questions/233507/how-to-log-out-user-from-web-site-using-basic-authentication/233551#233551
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Incorrect email or password",
#         headers={"WWW-Authenticate": "Basic"},
#     )


# @router.get("/protected")
# def protected_route(user: Annotated[dict, Depends(manager)]):
#     return {"user": user}


@router.get("/", tags=["index"])
async def root() -> HTMLResponse:
    content = Path(settings.PROJECT_PATH, "index.html").read_text(
        encoding="utf8"
    )

    return HTMLResponse(content=content)
