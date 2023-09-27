#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# curd/curd.py
# 数据库操作

from .connect import AsyncSessionMaker
from .model import Pay, User, Config, Msg
from app.schemas import Epusdt
from typing import Optional, List, Sequence, Union, Tuple

# sqlalchemy type
from sqlalchemy import (
    ForeignKey,
    func,
    select,
    update,
    String,
    DateTime,
)

from sqlalchemy.ext.asyncio import AsyncSession

# generate AsyncSession in function

# async def getUserByID(user_id: int) -> Optional[User]:
#     async with AsyncSessionMaker() as session:
#         result = await session.get(User, ident=user_id)
#         return result
# async def registerUser(user: User) -> User:
#     async with AsyncSessionMaker() as session:
#         pass


# async def getUserByID(session: AsyncSession, user_id: int) -> Optional[User]:


# 1. 机器人请求支付 将返回的 trade_id 和 user_id 入库
# 2. 支付成功后,接收回调,根据 trade_id 更新状态


class UserCurd(object):
    "针对 users 的 CURD"

    @staticmethod
    async def getUserByID(
        session: AsyncSession, user_id: Union[str, int]
    ) -> Optional[User]:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def registerUser(session: AsyncSession, user: User) -> User:
        check_exist = await UserCurd.getUserByID(session, user_id=user.user_id)
        if check_exist:
            return check_exist

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def getUserAmount(
        session: AsyncSession, user_id: Union[str, int]
    ) -> Optional[int]:
        user = await UserCurd.getUserByID(session, user_id=user_id)
        if user:
            return user.amount

    @staticmethod
    async def setUserAmount(
        session: AsyncSession, user_id: Union[str, int], value: float
    ) -> Optional[User]:
        origin_amount = await UserCurd.getUserAmount(session, user_id=user_id)
        if origin_amount:
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(amount=origin_amount + value)
            )
            return await UserCurd.getUserByID(session, user_id=user_id)

        return None


class PayCurd(object):
    """针对 pays 的 CURD"""

    @staticmethod
    async def createNewPay(session: AsyncSession, pay: Pay) -> Pay:
        """发起一个支付"""
        session.add(pay)
        await session.commit()
        await session.refresh(pay)
        return pay

    @staticmethod
    async def findPayByTradeID(
        session: AsyncSession, trade_id: str
    ) -> Optional[Pay]:
        result = await session.execute(
            select(Pay).where(Pay.trade_id == trade_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def updatePayStatus(
        session: AsyncSession, epusdt: Epusdt
    ) -> Optional[Tuple[Pay, Optional[User]]]:
        """更新订单状态并操作用户的余额"""
        pay = await PayCurd.findPayByTradeID(session, trade_id=epusdt.trade_id)
        if pay:
            await session.execute(
                update(Pay)
                .where(Pay.id == pay.id)
                .values(**epusdt.model_dump())
            )
            await session.refresh(pay)
            user = await UserCurd.setUserAmount(
                session, user_id=pay.user_id, value=pay.amount
            )
            return (pay, user)

        return None
