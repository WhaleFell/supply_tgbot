#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# bot router 机器人配置路由

from fastapi import APIRouter, Depends, Form, Body
from fastapi.responses import ORJSONResponse
from fastapi.encoders import jsonable_encoder

from typing_extensions import Annotated

from app.database.curd import ConfigCurd
import app.schemas
import app.database.model
from app.database.connect import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/config_get", tags=["config"], description="获取参数")
async def get_config(
    db: Annotated[AsyncSession, Depends(get_session)]
) -> app.schemas.Config:
    config = await ConfigCurd.getConfig(session=db)

    return app.schemas.Config.model_validate(config)


@router.post("/config_set", tags=["config"], description="配置参数")
async def set_config(
    data: Annotated[app.schemas.Config, Body(title="配置参数")],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> app.schemas.Config:
    set_config = app.database.model.Config(id=1, **data.model_dump())

    new_config = await ConfigCurd.updateConfig(session=db, config=set_config)
    await ConfigCurd.setUSDTToken(session=db)

    return app.schemas.Config.model_validate(new_config, from_attributes=True)


@router.get("/config_reset", tags=["config"], description="重置参数")
async def reset_config(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> app.schemas.Config:
    reset_config = await ConfigCurd.resetConfig(session=db)

    return app.schemas.Config.model_validate(reset_config, from_attributes=True)
