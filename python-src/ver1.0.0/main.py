import os
import base64, hashlib, hmac
import logging

from flask import abort, jsonify

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    LocationMessage, LocationAction,
    QuickReply, QuickReplyButton,
    ImageSendMessage
)

from logging import getLogger, DEBUG
import google.cloud.logging

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logger = getLogger(__name__)
logger.setLevel(DEBUG)

def main(request):
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
    channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

    line_bot_api = LineBotApi(channel_access_token)
    parser = WebhookParser(channel_secret)

    body = request.get_data(as_text=True)
    hash = hmac.new(channel_secret.encode('utf-8'),
        body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode()

    if signature != request.headers['X_LINE_SIGNATURE']:
        return abort(405)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return abort(405)


    for event in events:
        if isinstance(event.message, LocationMessage):
            logger.debug("Get Location Message")
            latitude = event.message.latitude
            longitude = event.message.longitude
            text_0 = "緯度 : {}, 経度 : {}\n".format(latitude, longitude)
            text_1 = "https://www.google.com/maps?q={},{}\n".format(latitude, longitude)
            messages = TextSendMessage(text= text_0 + text_1)
            line_bot_api.reply_message(event.reply_token, messages=messages)
        else :
            logger.debug("Get Text Message")
            if event.message.text == "位置情報":
                place = [QuickReplyButton(action=LocationAction(label="現在地を送信"))]
                messages = TextSendMessage(text="📍現在地📍を送信してください", quick_reply=QuickReply(items=place))
                line_bot_api.reply_message(event.reply_token, messages=messages)
            elif event.message.text == "画像":
                original_content_url = "https://raw.githubusercontent.com/yarakigit/line-bot-tutorial/main/line-bot-img-dir/tutorial/white_1024.png"
                preview_image_url    = "https://raw.githubusercontent.com/yarakigit/line-bot-tutorial/main/line-bot-img-dir/tutorial/white_240.png"
                messages = ImageSendMessage(original_content_url=original_content_url, preview_image_url=preview_image_url)
                line_bot_api.reply_message(event.reply_token, messages=messages)
            else:
                messages = TextSendMessage(text=event.message.text)
                line_bot_api.reply_message(event.reply_token, messages=messages)
       
    return jsonify({ 'message': 'ok'})