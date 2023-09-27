#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# schemas/epusdt.py
# epusdt 回调模型
from pydantic import Field, BaseModel, ConfigDict

"""
{
    "trade_id": "202203251648208648961728",
    "order_id": "2022123321312321321",
    "amount": 100,
    "actual_amount": 15.625,
    "token": "TNEns8t9jbWENbStkQdVQtHMGpbsYsQjZK",
    "block_transaction_id": "123333333321232132131",
    "signature": "xsadaxsaxsa",
    "status": 2
}
"""


class Epusdt(BaseModel):
    trade_id: str = Field(description="交易号")  # 入数据库
    order_id: str = Field(description="请求支付订单号")
    amount: float = Field(description="支付金额")
    actual_amount: float = Field(description="实际交易金额")
    token: str = Field(description="入账钱包地址")
    block_transaction_id: str = Field(description="交易区块号")
    signature: str = Field(description="签名")
    status: int = Field(description="订单状态 1:等待支付 2:支付成功 3:已过期")
