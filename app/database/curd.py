#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# curd/curd.py
# 数据库操作

from .connect import AsyncSessionMaker
from .model import Pay, User, Config, Msg
from app.schemas import Epusdt
from typing import Optional, List, Sequence, Union, Tuple
from app.utils.custom_log import logger

# sqlalchemy type
from sqlalchemy import (
    ForeignKey,
    func,
    select,
    update,
    String,
    DateTime,
    text,
    delete,
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


class ConfigCurd(object):
    """针对 config 的 CURD"""

    @staticmethod
    async def getConfig(session: AsyncSession) -> Config:
        result = await session.execute(select(Config).where(Config.id == 1))
        return result.scalar_one()

    @staticmethod
    async def updateConfig(session: AsyncSession, config: Config) -> Config:
        await session.execute(
            update(Config)
            .where(Config.id == 1)
            .values(**config.columns_to_dict())
        )
        await session.commit()

        return await ConfigCurd.getConfig(session)

    @staticmethod
    async def resetConfig(session: AsyncSession) -> Config:
        """重置参数"""
        await session.execute(delete(Config))
        default_config = Config(id=1)
        session.add(default_config)
        await session.commit()
        await session.refresh(default_config)
        return default_config

    @staticmethod
    async def setUSDTToken(session: AsyncSession):
        """去到 epusdt 的数据库修改钱包地址"""
        config: Config = await ConfigCurd.getConfig(session)

        await session.execute(
            text(
                f"UPDATE `epusdt`.`wallet_address` SET `token` = '{config.usdt_token}' WHERE `id` = 1"
            )
        )
        await session.commit()


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
    ) -> Optional[float]:
        user = await UserCurd.getUserByID(session, user_id=user_id)
        if user:
            return user.amount

    @staticmethod
    async def getUserCount(
        session: AsyncSession, user_id: Union[str, int]
    ) -> int:
        user = await UserCurd.getUserByID(session, user_id=user_id)
        if user:
            return user.count
        return 0

    @staticmethod
    async def setUserAmount(
        session: AsyncSession, user_id: Union[str, int], value: float
    ) -> Optional[User]:
        origin_amount = await UserCurd.getUserAmount(session, user_id=user_id)
        if origin_amount or origin_amount == 0:
            logger.success(
                f"操作金额中: Origin:{origin_amount} Value:{value} Result:{origin_amount + value}"
            )
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(amount=origin_amount + value)
            )
            await session.commit()
            return await UserCurd.getUserByID(session, user_id=user_id)

        return None

    @staticmethod
    async def addUserCount(
        session: AsyncSession, user_id: Union[str, int]
    ) -> Optional[User]:
        """发布次数 +1"""
        origin_count = await UserCurd.getUserCount(session, user_id=user_id)
        if origin_count or origin_count == 0:
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(count=origin_count + 1)
            )
            await session.commit()
            return await UserCurd.getUserByID(session, user_id=user_id)

        return None

    @staticmethod
    async def pay(session: AsyncSession, user: User) -> User:
        """增加一次次数并扣除对应的金额,返回用户对象"""
        config = await ConfigCurd.getConfig(session)
        await UserCurd.setUserAmount(
            session, user_id=user.user_id, value=-config.once_cost
        )
        await UserCurd.addUserCount(session, user_id=user.user_id)

        await session.commit()
        await session.refresh(user)

        return user


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
    ) -> Tuple[Pay, User]:
        """更新订单状态并操作用户的余额"""
        pay = await PayCurd.findPayByTradeID(session, trade_id=epusdt.trade_id)
        if pay:
            await session.execute(
                update(Pay)
                .where(Pay.id == pay.id)
                .values(
                    **epusdt.model_dump(
                        exclude={
                            "block_transaction_id",
                            "token",
                            "order_id",
                            "actual_amount",
                            "signature",
                        }
                    )
                )
            )
            await session.commit()
            await session.refresh(pay)
            user = await UserCurd.setUserAmount(
                session, user_id=pay.user_id, value=pay.amount
            )
            return (pay, user)  # type: ignore

        return None  # type: ignore

    @staticmethod
    async def getAllPay(
        session: AsyncSession,
    ) -> Union[List[Pay], Sequence[Pay]]:
        """获取所有的支付记录"""
        result = await session.scalars(select(Pay))
        return result.all()


class MsgCURD(object):
    """针对 msgs 表的 curd"""

    @staticmethod
    async def addMsg(session: AsyncSession, msg: Msg):
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg
