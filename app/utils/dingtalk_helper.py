import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
from app.models.database import SystemConfig

logger = logging.getLogger('db_monitor')

def send_dingtalk_message(title, text):
    try:
        webhook_url = SystemConfig.query.filter_by(key='dingtalk_webhook').first()
        secret_key = SystemConfig.query.filter_by(key='dingtalk_secret').first()

        if not webhook_url or not webhook_url.value:
            logger.warning("DingTalk webhook not configured")
            return False

        url = webhook_url.value
        secret = secret_key.value if secret_key else ''

        if secret:
            timestamp = str(round(time.time() * 1000))
            secret_enc = secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            
            if '?' in url:
                url = f"{url}&timestamp={timestamp}&sign={sign}"
            else:
                url = f"{url}?timestamp={timestamp}&sign={sign}"

        headers = {'Content-Type': 'application/json'}
        content = {
            "msgtype": "text",
            "text": {
                "content": f"{title}\n\n{text}"
            }
        }

        response = requests.post(url, headers=headers, data=json.dumps(content))
        result = response.json()
        
        if result.get('errcode') == 0:
            logger.info("DingTalk message sent")
            return True
        else:
            logger.error(f"DingTalk error: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send DingTalk message: {e}")
        return False

