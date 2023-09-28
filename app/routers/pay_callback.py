#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pay_callback router 路由
# 接收来自 epusdt 的回调
# https://github.com/assimon/epusdt/blob/master/wiki/API.md
from fastapi import APIRouter, HTTPException, status
from fastapi import Query, Body, Depends, Form
from fastapi.responses import PlainTextResponse, ORJSONResponse
from fastapi.encoders import jsonable_encoder
from typing_extensions import Annotated
from typing import List, Optional, Union, Dict
from datetime import timedelta, datetime

from app.config import settings
from app.utils.custom_log import logger
from app.schemas import Epusdt
from app.database.connect import get_session
from app.database.curd import PayCurd
from app.database.model import Pay, User

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/callback/", description="Epusdt 的回调地址")
async def handle_epusdt_callback(
    data: Annotated[Epusdt, Body(title="Epusdt 请求回调")],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PlainTextResponse:
    """
    只有支付成功后才会回调,必须只能返回字符串 ok
    """
    logger.info(f"接收到回调:{data}")
    pay, user = await PayCurd.updatePayStatus(session=db, epusdt=data)
    logger.success(
        f"ADD Amount:{str(pay.amount)} status:{str(pay.status)} ==> {str(user.user_id)}-{str(user.username)}-{str(user.amount)}"
    )

    return PlainTextResponse(content="ok")


@router.post("/get_all_pay/", description="获取所有支付记录")
async def get_all_pay(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ORJSONResponse:
    pays = await PayCurd.getAllPay(session=db)

    return ORJSONResponse(content=jsonable_encoder(pays))
