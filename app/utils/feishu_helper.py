import requests
import json
import time
import hashlib
import base64
import hmac
import logging
from app.models.database import SystemConfig

logger = logging.getLogger('db_monitor')

def gen_sign(secret, timestamp):
    """飞书签名生成 - 参考官方文档"""
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        b"",  # 空消息体
        digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign

def send_feishu_message(title, text):
    try:
        webhook_url = SystemConfig.query.filter_by(key='feishu_webhook').first()
        secret_key = SystemConfig.query.filter_by(key='feishu_secret').first()

        if not webhook_url or not webhook_url.value:
            logger.warning("Feishu webhook not configured")
            return False

        url = webhook_url.value
        secret = secret_key.value if secret_key else ''

        headers = {'Content-Type': 'application/json'}
        
        # Construct message
        content = {
            "msg_type": "text",
            "content": {
                "text": f"{title}\n\n{text}"
            }
        }

        if secret:
            timestamp = int(time.time())
            sign = gen_sign(secret, timestamp)
            content["timestamp"] = str(timestamp)
            content["sign"] = sign

        response = requests.post(url, headers=headers, data=json.dumps(content))
        result = response.json()
        
        if result.get('code') == 0:
            logger.info("Feishu message sent")
            return True
        else:
            logger.error(f"Feishu error: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send Feishu message: {e}")
        return False
