#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# curd/string_template.py
# 文字模板
from dataclasses import dataclass
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


# parameter
# 【普通供需消耗USDT】
# 【图文供需消耗USDT】
# 【发表次数】
# 【当前时间】
# 【用户内容】

from datetime import datetime, timedelta


def getBeijingTime() -> datetime:
    """获取北京时间"""
    utc_now = datetime.utcnow()  # 获取当前UTC时间
    beijing_offset = timedelta(hours=8)  # 北京时间比UTC时间早8小时
    beijing_now = utc_now + beijing_offset  # 将偏移量加到当前时间上
    return beijing_now


class CustomParam(BaseModel):
    costAmount: Optional[int] = None
    picCostAmount: Optional[int] = None
    count: Optional[int] = None
    currentTime: datetime = Field(default_factory=getBeijingTime)
    sendCountent: Optional[str] = None


@dataclass
class StringTemplate:
    description: str = """发布规则:

**💥本系统支持普通供需和图文供需：💥**
普通供需一次消耗 【普通供需消耗USDT】 USDT 
图文供需一次消耗【图文供需消耗USDT】USDT

发布付费广告严格要求如下
1：行数限制15行内【超过百分百不通过】
2：禁止发布虚假内容，禁止诈骗欺骗用户🚫
3：无需备注累计广告次数，机器人会自动统计

请编写好广告词，点击下方【📝自助发布】

供给频道： https://t.me/gcccaasas
"""
    # 供应文案
    provide_desc: str = """项目名称：
项目介绍：
价格：
联系人：
频道：【选填/没频道可以不填】
"""

    # 需求文案
    require_desc: str = """需求：
预算：
联系人：
频道：【选填/没频道可以不填】
"""

    send_content: str = """【用户内容】

该用户累计发布 【发表次数】 次，当前时间：【当前时间】
"""
