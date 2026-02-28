import requests
import json
import logging
from app.models.database import SystemConfig

logger = logging.getLogger('db_monitor')

def send_wechat_message(title, text):
    """
    Send message to WeChat Work (Enterprise WeChat) via webhook.
    """
    try:
        webhook_url_config = SystemConfig.query.filter_by(key='wechat_webhook').first()
        if not webhook_url_config or not webhook_url_config.value:
            logger.warning("WeChat webhook URL not configured.")
            return False
            
        webhook_url = webhook_url_config.value
        
        headers = {'Content-Type': 'application/json'}
        content = {
            "msgtype": "text",
            "text": {
                "content": f"{title}\n\n{text}"
            }
        }
        
        response = requests.post(webhook_url, headers=headers, data=json.dumps(content))
        result = response.json()
        
        if result.get('errcode') == 0:
            return True
        else:
            logger.error(f"WeChat API Error: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send WeChat message: {e}")
        return False

