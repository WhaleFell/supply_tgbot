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
from typing import List, Dict, Optional, Mapping
from typing_extensions import Annotated
from datetime import datetime, timedelta

# sqlalchemy type
from sqlalchemy import (
    ForeignKey,
    func,
    select,
    update,
    String,
    DateTime,
    Integer,
    Float,
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

from .string_template import StringTemplate

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
    amount: Mapped[int] = mapped_column(
        Integer(), nullable=False, comment="用户余额", default=0
    )

    # 注册时间,由数据库生成
    create_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
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

    once_cost: Mapped[int] = mapped_column(
        Integer,
        default=2,
        comment="一次发送消耗的 USDT",
    )

    channel_id: Mapped[str] = mapped_column(
        String(20), comment="机器人绑定的频道 ID", nullable=True
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
        String(20), ForeignKey("users.id"), comment="发送的用户ID"
    )

    content: Mapped[str] = mapped_column(
        String(1000), comment="发送的内容", nullable=False
    )


class Pay(Base):
    __tablename__ = "pays"
    __table_args__ = {"comment": "支付记录表"}

    # 数据库主键
    id: Mapped[IDPK]

    user_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("users.id"), comment="支付的用户 ID"
    )

    # 唯一订单号
    trade_id: Mapped[str] = mapped_column(
        String(100), comment="订单号", unique=True
    )

    amount: Mapped[float] = mapped_column(Float(precision=2), comment="金额")

    pay_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="交易时间 自动生成自动更新",
    )

    status: Mapped[int] = mapped_column(
        Integer, comment="交易状态 1:等待支付 2:支付成功 3:已过期", default=1
    )
