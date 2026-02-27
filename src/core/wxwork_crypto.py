#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业微信消息加解密
"""

import base64
import hashlib
import random
import string
import struct
import time
from Crypto.Cipher import AES


class WXBizMsgCrypt:
    """企业微信消息加解密"""

    def __init__(self, token, encoding_aes_key, corp_id):
        self.token = token
        self.key = base64.b64decode(encoding_aes_key + "=")
        self.corp_id = corp_id

    def VerifyURL(self, msg_signature, timestamp, nonce, echostr):
        """验证URL"""
        signature = self._generate_signature(timestamp, nonce, echostr)
        if signature != msg_signature:
            return -40001, None

        ret, decrypted = self._decrypt(echostr)
        if ret != 0:
            return ret, None

        return 0, decrypted

    def DecryptMsg(self, post_data, msg_signature, timestamp, nonce):
        """解密消息"""
        import xml.etree.ElementTree as ET
        root = ET.fromstring(post_data)
        encrypt = root.find("Encrypt").text

        signature = self._generate_signature(timestamp, nonce, encrypt)
        if signature != msg_signature:
            return -40001, None

        ret, decrypted = self._decrypt(encrypt)
        if ret != 0:
            return ret, None

        return 0, decrypted

    def _generate_signature(self, timestamp, nonce, encrypt):
        """生成签名"""
        sort_list = [self.token, timestamp, nonce, encrypt]
        sort_list.sort()
        sha = hashlib.sha1()
        sha.update("".join(sort_list).encode('utf-8'))
        return sha.hexdigest()

    def _decrypt(self, encrypt_text):
        """解密"""
        try:
            cipher = AES.new(self.key, AES.MODE_CBC, self.key[:16])
            plain_text = cipher.decrypt(base64.b64decode(encrypt_text))

            # 去除补位字符
            pad = plain_text[-1]
            if isinstance(pad, str):
                pad = ord(pad)
            plain_text = plain_text[:-pad]

            # 去除16位随机字符串和4位消息长度
            content = plain_text[16:]
            xml_len = struct.unpack("!I", content[:4])[0]
            xml_content = content[4:xml_len + 4]
            from_corpid = content[xml_len + 4:].decode('utf-8')

            if from_corpid != self.corp_id:
                return -40005, None

            return 0, xml_content

        except Exception as e:
            return -40002, None

    def EncryptMsg(self, reply_msg, timestamp, nonce):
        """加密并生成回复报文"""
        try:
            nonce = nonce or self._get_random_str()
            timestamp = timestamp or str(int(time.time()))

            raw = (
                self._get_random_str().encode("utf-8")
                + struct.pack("!I", len(reply_msg))
                + reply_msg.encode("utf-8")
                + self.corp_id.encode("utf-8")
            )
            padded = self._pad(raw)

            cipher = AES.new(self.key, AES.MODE_CBC, self.key[:16])
            encrypt = base64.b64encode(cipher.encrypt(padded)).decode("utf-8")

            signature = self._generate_signature(timestamp, nonce, encrypt)
            resp_xml = (
                "<xml>"
                f"<Encrypt><![CDATA[{encrypt}]]></Encrypt>"
                f"<MsgSignature><![CDATA[{signature}]]></MsgSignature>"
                f"<TimeStamp>{timestamp}</TimeStamp>"
                f"<Nonce><![CDATA[{nonce}]]></Nonce>"
                "</xml>"
            )
            return 0, resp_xml
        except Exception:
            return -40006, None

    @staticmethod
    def _get_random_str(length=16):
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def _pad(text):
        block_size = 32
        pad_amount = block_size - (len(text) % block_size)
        pad_char = bytes([pad_amount])
        return text + pad_char * pad_amount

