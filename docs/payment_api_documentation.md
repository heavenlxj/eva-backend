# 支付相关接口文档

## 支付订单接口

### 1. 创建支付订单
- **接口名称**: 创建支付订单
- **请求方式**: POST
- **URL路径**: `/app/api/payment/order`
- **需要认证**: 是（Bearer Token）
- **Request Body**:
```json
{
  "pay_type": "jsapi",              // 支付类型：jsapi(小程序支付)/native(扫码支付)/h5(H5支付)
  "amount": 10000,                  // 订单金额（单位：分），例如：10000 = 100元
  "payer": "openid_xxx",            // 支付者openid（JSAPI支付时需要，可选）
  "payment_method": "wechat_pay",   // 支付方式：wechat_pay(微信支付)/virtual_currency(虚拟币)，默认wechat_pay
  "is_recharge": false              // 是否为充值订单：true(充值)/false(商品购买)，默认false
}
```
- **Response 样例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "code": 200,
    "message": {
      "prepay_id": "wx0416014858695039xxxxx"
    },
    "order": {
      "id": 123,
      "order_id": "a1b2c3d4e5f6g7h8",
      "user_id": "user_123",
      "amount": 10000,
      "currency": "CNY",
      "status": "created",
      "message": "{\"prepay_id\":\"wx0416014858695039xxxxx\"}",
      "pay_type": "jsapi",
      "payment_method": "wechat_pay",
      "order_type": "product",
      "virtual_currency_amount": null,
      "transaction_id": null,
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  }
}
```

### 2. 签名支付参数
- **接口名称**: 签名支付参数
- **请求方式**: POST
- **URL路径**: `/app/api/payment/sign`
- **需要认证**: 是（Bearer Token）
- **Request Body**:
```json
{
  "app_id": "wx15daec1f510897c4",           // 小程序AppID
  "time_stamp": "1704067200",               // 时间戳（秒）
  "nonce": "5K8264ILTKCH16CQ2502SI8ZNMTM67VS",  // 随机字符串
  "package": "prepay_id=wx0416014858695039xxxxx"  // 订单详情扩展字符串
}
```
- **Response 样例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "signature": "C380BEC2BFD727A4B6845133519F3AD6"
  }
}
```

### 3. 查询订单
- **接口名称**: 查询订单
- **请求方式**: GET
- **URL路径**: `/app/api/payment/order/{order_id}`
- **需要认证**: 是（Bearer Token）
- **Request Parameter**:
  - `order_id` (path): 订单号，例如：`a1b2c3d4e5f6g7h8`
- **Response 样例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 123,
    "order_id": "a1b2c3d4e5f6g7h8",
    "user_id": "user_123",
    "amount": 10000,
    "currency": "CNY",
    "status": "paid",
    "message": null,
    "pay_type": "jsapi",
    "payment_method": "wechat_pay",
    "order_type": "recharge",
    "virtual_currency_amount": null,
    "transaction_id": "wx_transaction_123456789",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:05:00"
  }
}
```

### 4. 微信支付回调
- **接口名称**: 微信支付回调
- **请求方式**: POST
- **URL路径**: `/app/api/payment/wx-notify`
- **需要认证**: 否（微信服务器调用）
- **Request Headers**:
  - `Wechatpay-Signature`: 微信支付签名
  - `Wechatpay-Timestamp`: 时间戳
  - `Wechatpay-Nonce`: 随机字符串
  - `Wechatpay-Serial`: 证书序列号
- **Request Body**: 微信支付回调的加密数据（字节流）
- **Response 样例**:
```json
{
  "code": "SUCCESS",
  "message": "成功"
}
```

---

## 虚拟币接口

### 5. 获取虚拟币余额
- **接口名称**: 获取虚拟币余额
- **请求方式**: GET
- **URL路径**: `/app/api/virtual-currency/balance`
- **需要认证**: 是（Bearer Token）
- **Request Parameter**: 无
- **Response 样例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "balance": 1000,              // 当前余额（单位：代币，1人民币=10代币）
    "frozen_balance": 0,           // 冻结余额（单位：代币）
    "total_recharged": 10000,      // 累计充值金额（单位：分）
    "total_consumed": 500         // 累计消费虚拟币（单位：代币）
  }
}
```

### 6. 获取虚拟币交易记录
- **接口名称**: 获取虚拟币交易记录
- **请求方式**: GET
- **URL路径**: `/app/api/virtual-currency/transactions`
- **需要认证**: 是（Bearer Token）
- **Request Parameter**:
  - `transaction_type` (query, 可选): 交易类型，可选值：`recharge`(充值)/`consume`(消费)/`refund`(退款)
  - `limit` (query, 可选): 每页数量，默认50，范围1-100
  - `offset` (query, 可选): 偏移量，默认0
- **Response 样例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "transactions": [
      {
        "id": 1,
        "transaction_type": "recharge",
        "amount": 1000,
        "balance_before": 0,
        "balance_after": 1000,
        "order_id": "a1b2c3d4e5f6g7h8",
        "description": "充值 100.00 元，获得 1000 代币",
        "status": "success",
        "created_at": "2024-01-01T12:00:00"
      },
      {
        "id": 2,
        "transaction_type": "consume",
        "amount": -500,
        "balance_before": 1000,
        "balance_after": 500,
        "order_id": "b2c3d4e5f6g7h8i9",
        "description": "消费 500 代币",
        "status": "success",
        "created_at": "2024-01-01T13:00:00"
      }
    ],
    "total": 2
  }
}
```

---

## 接口使用场景说明

### 场景1：用户微信支付充值虚拟币
1. 调用 **创建支付订单** (`POST /app/api/payment/order`)，设置 `is_recharge=true`, `payment_method="wechat_pay"`
2. 调用 **签名支付参数** (`POST /app/api/payment/sign`)，获取签名
3. 小程序调起微信支付
4. 微信支付成功后，自动调用 **微信支付回调** (`POST /app/api/payment/wx-notify`)
5. 系统自动充值虚拟币到用户账户
6. 调用 **获取虚拟币余额** (`GET /app/api/virtual-currency/balance`) 查看余额

### 场景2：用户使用虚拟币购买商品
1. 调用 **创建支付订单** (`POST /app/api/payment/order`)，设置 `payment_method="virtual_currency"`, `is_recharge=false`
2. 系统自动扣减虚拟币，订单状态直接为 `paid`
3. 调用 **获取虚拟币余额** (`GET /app/api/virtual-currency/balance`) 查看余额变化

### 场景3：用户微信支付购买商品
1. 调用 **创建支付订单** (`POST /app/api/payment/order`)，设置 `is_recharge=false`, `payment_method="wechat_pay"`
2. 调用 **签名支付参数** (`POST /app/api/payment/sign`)，获取签名
3. 小程序调起微信支付
4. 微信支付成功后，自动调用 **微信支付回调** (`POST /app/api/payment/wx-notify`)
5. 订单状态更新为 `paid`

### 场景4：查询订单和交易记录
1. 调用 **查询订单** (`GET /app/api/payment/order/{order_id}`) 查看订单详情
2. 调用 **获取虚拟币交易记录** (`GET /app/api/virtual-currency/transactions`) 查看交易流水

---

## 错误响应格式

所有接口在出错时返回统一格式：
```json
{
  "code": 1,
  "message": "错误信息描述",
  "data": null
}
```

常见错误码：
- `code: 0` - 成功
- `code: 1` - 业务错误（具体错误信息在 message 中）
- HTTP 状态码：
  - `200` - 成功
  - `400` - 请求参数错误
  - `401` - 未认证
  - `403` - 无权限
  - `404` - 资源不存在
  - `500` - 服务器内部错误

