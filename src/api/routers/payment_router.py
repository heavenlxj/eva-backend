# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @File    : payment_router.py

# from fastapi import APIRouter, Request, Response, status, Query, Depends
# from typing import Optional
# from loguru import logger

# from entity.base import BaseResponse, PageResponse
# from entity.payment import PayRequest, SignRequest, OrderResponse, CreateOrderResponse
# from entity.pagination import PageParams
# from auth import AuthUser
# from db_wrapper import DB_SESSION
# from services.payment import PaymentService
# from core.middleware import skip_client_verification_for_router

# payment_router = skip_client_verification_for_router(APIRouter(prefix="/payment", tags=["payment"]))


# @payment_router.post("/order", response_model=BaseResponse)
# async def create_order(
#     pay_request: PayRequest,
#     user: AuthUser,
#     db: DB_SESSION
# ):
#     """创建支付订单"""
#     try:
#         service = PaymentService(db)
#         result = await service.create_order(
#             user_id=user.user_id,
#             amount=pay_request.amount,
#             pay_type=pay_request.pay_type,
#             payer=pay_request.payer,
#             payment_method=pay_request.payment_method or "wechat_pay",
#             is_recharge=pay_request.is_recharge or False
#         )
        
#         order_response = OrderResponse.model_validate(result["order"])
#         return BaseResponse.success({
#             "code": result["code"],
#             "message": result["message"],
#             "order": order_response.model_dump()
#         })
#     except Exception as e:
#         logger.error(f"创建订单失败, userId={user.user_id}: {e}")
#         return BaseResponse.error_with_msg(message=f"创建订单失败: {str(e)}")


# @payment_router.post("/sign", response_model=BaseResponse)
# async def sign_payment(
#     sign_request: SignRequest,
#     user: AuthUser,
#     db: DB_SESSION
# ):
#     """对支付参数进行签名"""
#     try:
#         service = PaymentService(db)
#         signature = await service.sign_payment(
#             app_id=sign_request.app_id,
#             time_stamp=sign_request.time_stamp,
#             nonce=sign_request.nonce,
#             package=sign_request.package
#         )
#         return BaseResponse.success({"signature": signature})
#     except Exception as e:
#         logger.error(f"签名失败, userId={user.user_id}: {e}")
#         return BaseResponse.error_with_msg(message=f"签名失败: {str(e)}")


# @payment_router.get("/order/{order_id}", response_model=BaseResponse)
# async def get_order(
#     order_id: str,
#     user: AuthUser,
#     db: DB_SESSION
# ):
#     """查询订单"""
#     try:
#         service = PaymentService(db)
#         order = await service.get_order(order_id)
        
#         if order is None:
#             return BaseResponse.error_with_msg(message="订单不存在")
        
#         # 验证订单是否属于当前用户
#         if order.user_id != user.user_id:
#             return BaseResponse.error_with_msg(message="无权访问该订单")
        
#         order_response = OrderResponse.model_validate(order)
#         return BaseResponse.success(order_response.model_dump())
#     except Exception as e:
#         logger.error(f"查询订单失败, userId={user.user_id}: {e}")
#         return BaseResponse.error_with_msg(message=f"查询订单失败: {str(e)}")


# @payment_router.get("/orders", response_model=PageResponse[OrderResponse])
# async def get_order_list(
#     user: AuthUser,
#     db: DB_SESSION,
#     status: Optional[str] = Query(None, description="订单状态：created/paid/failed/cancelled"),
#     order_type: Optional[str] = Query(None, description="订单类型：recharge/product"),
#     payment_method: Optional[str] = Query(None, description="支付方式：wechat_pay/virtual_currency"),
#     sort_by: Optional[str] = Query("created_at", description="排序字段"),
#     order: Optional[str] = Query("desc", description="排序方向：asc/desc"),
#     page: PageParams = Depends(),
# ):
#     """获取订单列表（支持分页）"""
#     try:
#         service = PaymentService(db)

#         order_list = await service.get_order_list(
#             user_id=user.user_id,
#             status=status,
#             order_type=order_type,
#             payment_method=payment_method,
#             page=page.page,
#             page_size=page.page_size,
#             sort_by=sort_by,
#             order=order,
#         )
        
#         # 将 Order 对象转换为 OrderResponse
#         order_responses = [OrderResponse.model_validate(order) for order in order_list.items]
#         # 创建新的 Page 对象，包含转换后的 OrderResponse 列表
#         from entity.pagination import Page
#         order_page = Page[OrderResponse](
#             items=order_responses,
#             total=order_list.total,
#             page=order_list.page,
#             page_size=order_list.page_size,
#         )
#         return PageResponse[OrderResponse](data=order_page)
#     except Exception as e:
#         logger.error(f"获取订单列表失败, userId={user.user_id}: {e}")
#         from entity.pagination import Page
#         error_page = Page[OrderResponse](
#             items=[],
#             total=0,
#             page=page.page,
#             page_size=page.page_size,
#         )
#         return PageResponse[OrderResponse](
#             code=-1,
#             message=f"获取订单列表失败: {str(e)}",
#             data=error_page
#         )


# @payment_router.post("/wx-notify")
# async def wx_payment_notify(request: Request, response: Response, db: DB_SESSION):
#     """微信支付回调接口"""
#     try:
#         headers = dict(request.headers)
#         body = await request.body()
        
#         service = PaymentService(db)
#         result = await service.handle_payment_notify(headers, body)
        
#         if result["code"] == "SUCCESS":
#             return {"code": "SUCCESS", "message": "成功"}
#         else:
#             response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#             return {"code": "FAILED", "message": "失败"}
#     except Exception as e:
#         logger.error(f"处理支付回调失败: {e}")
#         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#         return {"code": "FAILED", "message": "失败", "error": str(e)}

