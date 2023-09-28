#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# schemas/user.py
# config 模型
from pydantic import ConfigDict, BaseModel, Field

"""
{
    "admin_password": "admin",
    "provide_desc": "\n项目名称：\n项目介绍：\n价格：\n联系人：\n频道：【选填/没频道可以不填】\n",
    "send_content": "\n【用户内容】\n\n该用户累计发布 【发表次数】 次，当前时间：【当前时间】\n",
    "channel_id": "-1001858197255",
    "usdt_token": "TTV9EnFgcZ8WXvE3YPqwz4VYoQzzLLLLLL",
    "description": "\n发布规则 付费广告 消耗 【每次消耗的USDT】 USDT\n\n发布付费广告严格要求如下\n1：行数限制15行内【超过百分百不通过】\n2：禁止发布虚假内容，禁止诈骗欺骗用户🚫\n3：无需备注累计广告次数，机器人会自动统计\n\n请编写好广告词，点击下方【📝自助发布】\n\n供给频道： https://t.me/gcccaasas\n",
    "id": 1,
    "require_desc": "\n需求：\n预算：\n联系人：\n频道：【选填/没频道可以不填】\n",
    "once_cost": 2
}
"""


class Config(BaseModel):
    admin_password: str = Field(title="后台密码", default="admin")
    provide_desc: str = Field(title="供给模板", default=None)
    require_desc: str = Field(title="需求模板", default=None)
    send_content: str = Field(title="发送模板", default=None)
    channel_id: str = Field(title="频道ID", default=None)
    usdt_token: str = Field(title="收款的 USDT 地址", default=None)
    description: str = Field(title="机器人描述", default=None)
    once_cost: float = Field(title="单价", default=None)

    model_config = ConfigDict(from_attributes=True)
