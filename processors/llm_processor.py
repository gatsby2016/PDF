import websocket
import datetime
import hashlib
import base64
import hmac
import json
import time
from urllib.parse import urlparse
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

from config import (
    XUNFEI_APP_ID,
    XUNFEI_API_KEY,
    XUNFEI_API_SECRET,
    XUNFEI_DOMAIN,
    XUNFEI_URL
)

class LLMProcessor:
    def __init__(self):
        self.app_id = XUNFEI_APP_ID
        self.api_key = XUNFEI_API_KEY
        self.api_secret = XUNFEI_API_SECRET
        self.domain = XUNFEI_DOMAIN
        self.spark_url = XUNFEI_URL
        
    def _create_url(self):
        """生成请求URL"""
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        # 解析URL
        parsed_url = urlparse(self.spark_url)
        
        # 构建待加密的字符串
        signature_origin = f"host: {parsed_url.netloc}\n"
        signature_origin += f"date: {date}\n"
        signature_origin += f"GET {parsed_url.path} HTTP/1.1"
        
        # 使用hmac-sha256进行加密
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        signature_sha_base64 = base64.b64encode(signature_sha).decode()
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", '
        authorization_origin += f'headers="host date request-line", signature="{signature_sha_base64}"'
        
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode()
        
        # 构建最终的URL
        v = {
            "authorization": authorization,
            "date": date,
            "host": parsed_url.netloc
        }
        url = self.spark_url + '?' + urlencode(v)
        return url

    def process_text(self, prompt, max_tokens=1000):
        """使用讯飞星火处理文本"""
        try:
            response_text = []
            
            def on_message(ws, message):
                data = json.loads(message)
                code = data['header']['code']
                if code != 0:
                    print(f'请求错误: {code}, {data}')
                    ws.close()
                else:
                    content = data['payload']['choices']['text'][0]['content']
                    response_text.append(content)
                    if data['header']['status'] == 2:
                        ws.close()
            
            def on_error(ws, error):
                print(f"错误: {error}")
                ws.close()
            
            def on_close(ws, close_status_code, close_msg):
                print("连接已关闭")
            
            def on_open(ws):
                data = {
                    "header": {
                        "app_id": self.app_id,
                        "uid": "12345"
                    },
                    "parameter": {
                        "chat": {
                            "domain": self.domain,
                            "temperature": 0.5,
                            "max_tokens": max_tokens
                        }
                    },
                    "payload": {
                        "message": {
                            "text": [
                                {"role": "system", "content": "您是一个专业科学编辑，擅长总结和分析科学论文。"},
                                {"role": "user", "content": prompt}
                            ]
                        }
                    }
                }
                ws.send(json.dumps(data))
            
            # 创建WebSocket连接
            ws = websocket.WebSocketApp(
                self._create_url(),
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            ws.run_forever()
            
            # 合并所有响应文本
            return ''.join(response_text).strip()
            
        except Exception as e:
            print(f"LLM处理时出错: {str(e)}")
            return "无法生成内容，请检查API配置或重试。"