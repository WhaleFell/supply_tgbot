#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# user router 路由


from fastapi import APIRouter, Depends, Query, status, Body
from fastapi.responses import ORJSONResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder

from typing_extensions import Annotated
from typing import Optional

from app.database.curd import UserCurd
import app.schemas
import app.database.model
from app.database.connect import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

router = APIRouter()


@router.get("/get_all_user/", description="获取所有用户")
async def get_all_user(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ORJSONResponse:
    users = await UserCurd.getAllUser(session=db)
    if users:
        return ORJSONResponse(content=jsonable_encoder(users))

    return ORJSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder([])
    )


@router.get("/get_user/", description="根据 userid 获取单个用户")
async def get_user(
    user_id: Annotated[str, Query(title="用户 ID")],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ORJSONResponse:
    user: Optional[app.database.User] = await UserCurd.getUserByID(
        session=db, user_id=user_id
    )
    if user:
        return ORJSONResponse(content=jsonable_encoder(user))

    return ORJSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder([])
    )


@router.get("/get_user_total_amount/", description="获取用户的总余额")
async def get_user_total_amount(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> PlainTextResponse:
    result = await db.execute(func.sum(app.database.model.User.amount))
    total: float = result.scalar()  # type: ignore

    return PlainTextResponse(content=str(round(total, 2)))


@router.post("/set_user_amount/", description="设置用户余额")
async def set_user_amount(
    user_id: Annotated[str, Body(title="用户 ID")],
    amount: Annotated[float, Body(title="用户 ID")],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ORJSONResponse:
    user = await UserCurd.setUserAmount(
        session=db, user_id=user_id, value=amount
    )
    if user:
        return ORJSONResponse(content=jsonable_encoder(user))

    return ORJSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder([])
    )
