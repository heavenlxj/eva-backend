#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : payment.py

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    order_id: str
    user_id: str
    amount: int
    currency: str = "CNY"
    status: str
    message: Optional[str] = None
    pay_type: Optional[str] = None
    payment_method: Optional[str] = None
    order_type: Optional[str] = None
    virtual_currency_amount: Optional[int] = None
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayRequest(BaseModel):
    """支付请求"""
    pay_type: str  # jsapi/native/h5
    amount: int # 金额（分）
    payer: Optional[str] = None  # 支付者openid（JSAPI需要）
    payment_method: Optional[str] = "wechat_pay"  # 支付方式：wechat_pay(微信支付)/virtual_currency(虚拟币)
    is_recharge: Optional[bool] = False  # 是否为充值订单（用于区分充值和商品购买）


class SignRequest(BaseModel):
    """签名请求"""
    app_id: str
    time_stamp: str
    nonce: str
    package: str


class CreateOrderResponse(BaseModel):
    """创建订单响应"""
    code: int
    message: str | dict
    order: OrderResponse