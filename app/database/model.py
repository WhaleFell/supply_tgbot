#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# curd/model.py
# 数据库模型

"""
参考文档:
    [1]: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#declarative-mapping
    [2]: https://docs.sqlalchemy.org/en/20/orm/declarative_config.html#mapper-configuration-options-with-declarative
    [3]: https://docs.sqlalchemy.org/en/20/orm/declarative_mixins.html#composing-mapped-hierarchies-with-mixins
    [4]: https://docs.sqlalchemy.org/en/20/orm/declarative_config.html#other-declarative-mapping-directives
"""
import asyncio
from typing import List, Dict, Optional, Mapping, Type, TypeVar, Tuple
import typing
from typing_extensions import Annotated
from datetime import datetime, timedelta

# sqlalchemy type
import sqlalchemy.orm
from sqlalchemy import (
    ForeignKey,
    func,
    select,
    update,
    String,
    DateTime,
    Integer,
    Float,
    Boolean,
)

# sqlalchemy asynchronous support
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    async_sessionmaker,
    AsyncSession,
    create_async_engine,
)

# sqlalchemy ORM
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

import inspect

from .string_template import StringTemplate, CustomParam, getBeijingTime

# 主键 ID
# https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#mapping-whole-column-declarations-to-python-types
# 将整个列声明映射到 Python 类型
# 但目前尝试使用 Annotated 来指示 relationship() 的进一步参数以及类似的操作将在运行时引发 NotImplementedError 异常，但是可能会在未来的版本中实现。
IDPK = Annotated[
    int,
    mapped_column(primary_key=True, autoincrement=True, comment="ID主键"),
]


class Base(AsyncAttrs, DeclarativeBase):
    """ORM 基类 | 详见[1]、[3]"""

    __table_args__ = {
        "mysql_engine": "InnoDB",  # MySQL引擎
        "mysql_charset": "utf8mb4",  # 设置表的字符集
        "mysql_collate": "utf8mb4_general_ci",  # 设置表的校对集
    }

    # def __repr__(self) -> str:
    #     cls = type(self).__name__
    #     fields = inspect.getmembers(self, lambda x: not inspect.isroutine(x))
    #     fields = [f for f in fields if not f[0].startswith("_")]
    #     args = ", ".join(f"{f[0]}={repr(f[1])}" for f in fields)
    #     return f"<{cls}({args})>"


from pyrogram.types import Message


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表"}

    # 数据库主键
    id: Mapped[IDPK]

    # 用户名
    username: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="用户名"
    )

    # 用户唯一 ID
    user_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="密码", unique=True
    )

    # 余额
    amount: Mapped[float] = mapped_column(
        Float(precision=2), nullable=False, comment="用户余额", default=0
    )

    # 注册时间,由数据库生成
    create_at: Mapped[datetime] = mapped_column(
        nullable=False,
        # server_default=func.now(),
        # default=getBeijingTime(),
        default=getBeijingTime,
        comment="注册时间",
    )

    # 发布次数
    count: Mapped[int] = mapped_column(
        nullable=False, default=0, comment="发布次数"
    )

    # 发送过的 Msg  一的一端
    msgs: Mapped[List["Msg"]] = relationship(
        "Msg", backref="users", lazy="subquery"
    )

    # 支付记录
    pays: Mapped[List["Pay"]] = relationship(
        "Pay", backref="users", lazy="subquery"
    )

    @classmethod
    def generateUser(cls: Type["User"], message: Message) -> "User":
        """根据信息生成 User 对象"""
        return cls(
            username=message.from_user.username,
            user_id=message.from_user.id,
        )

    def getUserPays(self) -> List[str]:
        """获取用户支付记录信息"""

        def generate_status(status: int) -> str:
            if status == 1:
                return "等待支付"
            elif status == 2:
                return "成功支付"
            elif status == 3:
                return "已经超时"
            return "未知"

        # success = [
        #     f"支付时间:{pay.pay_at}-金额:{pay.amount}"
        #     for pay in self.pays
        #     if pay.status == 2
        # ]

        # failure = [
        #     f"支付时间:{pay.pay_at}-金额:{pay.amount}-状态:{'已超时' if pay.status==3 else '等待支付'}"
        #     for pay in self.pays
        #     if pay.status != 2
        # ]

        all = [
            f"支付时间:{pay.pay_at}-金额:{pay.amount}-状态:{generate_status(pay.status)}-订单号:<code>{pay.trade_id}</code>"
            for pay in self.pays
        ]

        return all

    def getUserMsg(self) -> List[str]:
        all = [
            f"发送时间:{msg.send_at} 扣除金额:{msg.amount} 链接:{msg.url}"
            for msg in self.msgs
        ]
        return all

    def getUserLink(self) -> str:
        """获取用户链接如果不存在的返回用户ID"""
        if self.username:
            return f"[👉点击此处联系发布者👈](https://t.me/{self.username})"
        else:
            return f"发布者 ID:{self.user_id}"


class Config(Base):
    __tablename__ = "config"
    __table_args__ = {"comment": "配置表"}

    # 数据库主键
    id: Mapped[IDPK]

    admin_password: Mapped[str] = mapped_column(
        String(100), default="admin", comment="管理员密码"
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        default=StringTemplate.description,
        comment="机器人 /start 时的描述",
    )

    provide_desc: Mapped[str] = mapped_column(
        String(1000),
        default=StringTemplate.provide_desc,
        comment="供给方描述",
    )

    require_desc: Mapped[str] = mapped_column(
        String(1000),
        default=StringTemplate.require_desc,
        comment="需求方描述",
    )

    send_content: Mapped[str] = mapped_column(
        String(1000),
        default=StringTemplate.send_content,
        comment="发送频道描述",
    )

    once_cost: Mapped[float] = mapped_column(
        Float(precision=2),
        default=2,
        comment="一次发送普通供需消耗的 USDT",
    )

    pic_once_cost: Mapped[float] = mapped_column(
        Float(precision=2),
        default=5,
        comment="一次发送图文消耗的 USDT",
    )

    channel_ids: Mapped[str] = mapped_column(
        String(1000),
        comment="机器人需要发送的 channel ids 用逗号分隔",
        nullable=False,
        default="-1001558383712,",
    )

    usdt_token: Mapped[str] = mapped_column(
        String(100),
        comment="收款USDT地址",
        default="TTV9EnFgcZ8WXvE3YPqwz4VYoQzzLLLLLL",
    )

    ban_words: Mapped[str] = mapped_column(
        String(1000),
        comment="由逗号分隔的违禁词列表",
        default="做爱,死,数学,地理,生物,幼女,黄颖宝,蔡徐坤,陈立农,鸡巴",
    )

    multiple: Mapped[float] = mapped_column(
        Float(precision=2), comment="充值倍率", nullable=False, default=1.0
    )

    @property
    def banWordList(self) -> List[str]:
        """生成屏蔽词列表"""
        return self.ban_words.split(",")

    @property
    def sendChannelIDs(self) -> List[int]:
        """生成需要发送的频道列表"""
        # print(self.channel_ids.split(","))
        return [int(id_) for id_ in self.channel_ids.split(",") if id_ != ""]

    def replaceConfig(self, custom: CustomParam) -> "Config":
        # TODO: need optimize the code
        return Config(
            id=self.id,
            admin_password=self.admin_password,
            description=self.description.replace(
                "【普通供需消耗USDT】", str(self.once_cost)
            )
            .replace(
                "【当前时间】", custom.currentTime.strftime(r"%Y-%m-%d %H:%M:%S")
            )
            .replace("【图文供需消耗USDT】", str(self.pic_once_cost)),
            provide_desc=self.provide_desc,
            require_desc=self.require_desc,
            send_content=self.send_content.replace("【发表次数】", str(custom.count))
            .replace(
                "【当前时间】", custom.currentTime.strftime(r"%Y-%m-%d %H:%M:%S")
            )
            .replace("【用户内容】", str(custom.sendCountent)),
            once_cost=self.once_cost,
            channel_ids=self.channel_ids,
            multiple=self.multiple,
        )

    # https://stackoverflow.com/questions/1958219/how-to-convert-sqlalchemy-row-object-to-a-python-dict#34
    def columns_to_dict(self):
        dict_ = {}
        for key in self.__mapper__.c.keys():
            dict_[key] = getattr(self, key)
        return dict_


class Msg(Base):
    __tablename__ = "msgs"
    __table_args__ = {"comment": "发送记录表"}

    # 数据库主键
    id: Mapped[IDPK]

    user_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("users.user_id"), comment="发送的用户ID"
    )

    content: Mapped[str] = mapped_column(
        String(1000), comment="发送的内容", nullable=False
    )

    # 发送时间,由数据库生成
    send_at: Mapped[datetime] = mapped_column(
        nullable=False,
        # server_default=func.now(),
        default=getBeijingTime,
        comment="注册时间",
    )

    # 这条信息扣除的金额
    amount: Mapped[float] = mapped_column(
        Float(precision=2), comment="这条信息扣除的金额", nullable=False
    )

    # 发送返回的频道 URL
    url: Mapped[str] = mapped_column(
        String(1000), comment="发送返回的频道 URL,如果多个频道就用,链接", nullable=True
    )


class Pay(Base):
    __tablename__ = "pays"
    __table_args__ = {"comment": "支付记录表"}

    # 数据库主键
    id: Mapped[IDPK]

    user_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("users.user_id"), comment="支付的用户 ID"
    )

    # 唯一订单号
    trade_id: Mapped[str] = mapped_column(
        String(100), comment="订单号", unique=True
    )

    # 实际支付的金额
    amount: Mapped[float] = mapped_column(Float(precision=2), comment="实际支付的金额")

    pay_at: Mapped[datetime] = mapped_column(
        nullable=False,
        # server_default=func.now(),
        # default=getBeijingTime(),
        # onupdate=func.now(),
        default=getBeijingTime,
        onupdate=getBeijingTime,
        comment="交易时间 自动生成自动更新",
    )

    status: Mapped[int] = mapped_column(
        Integer, comment="交易状态 1:等待支付 2:支付成功 3:已过期", default=1
    )

    # 该交易是否了通知用户
    notice: Mapped[bool] = mapped_column(
        Boolean(), default=False, comment="该交易是否通知用户"
    )
