#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# bot router 机器人配置路由

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from fastapi.encoders import jsonable_encoder

from typing_extensions import Annotated

from app.database.curd import ConfigCurd
from app.schemas import BaseResp
from app.database.connect import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/get_config", tags=["bot"])
async def root(
    db: Annotated[AsyncSession, Depends(get_session)]
) -> ORJSONResponse:
    config = await ConfigCurd.getConfig(session=db)

    return ORJSONResponse(content=jsonable_encoder(config))
