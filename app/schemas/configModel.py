#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# schemas/user.py
# config 模型
from pydantic import ConfigDict, BaseModel, Field


class Config(BaseModel):
    admin_password: str = Field(title="后台密码", default="admin")
    provide_desc: str = Field(title="供给模板", default=None)
    require_desc: str = Field(title="需求模板", default=None)
    send_content: str = Field(title="发送模板", default=None)
    channel_ids: str = Field(title="频道ID 用 , 分隔", default=None)
    usdt_token: str = Field(title="收款的 USDT 地址", default=None)
    description: str = Field(title="机器人描述", default=None)
    once_cost: float = Field(title="普通文字供需单价", default=None)
    pic_once_cost: float = Field(title="图文供需单价", default=None)
    ban_words: str = Field(title="屏蔽词,使用 , 分隔", default=None)
    multiple: float = Field(title="倍率", default=None)
    model_config = ConfigDict(from_attributes=True)

    model_config = ConfigDict(from_attributes=True)
