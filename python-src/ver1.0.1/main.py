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
    MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage, LocationMessage, ImageSendMessage, TemplateSendMessage,
    QuickReply, QuickReplyButton, ButtonsTemplate,
    LocationAction, DatetimePickerTemplateAction
)

from logging import getLogger, DEBUG
import google.cloud.logging

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logger = getLogger(__name__)
logger.setLevel(DEBUG)

import datetime

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
        if isinstance(event, PostbackEvent):
            logger.debug("Get PostbackEvent")
            if event.postback.data == 'datetime-picker-action-postback':
                logger.debug("data : datetime-picker-action-postback")
                messages = TextSendMessage(text=event.postback.params['date'])#dictのキーはmodeのもの
                line_bot_api.reply_message(event.reply_token, messages=messages)
        elif isinstance(event, MessageEvent):
            logger.debug("Get MessageEvent")
            if isinstance(event.message, LocationMessage):
                logger.debug("Get Location Message")
                latitude = event.message.latitude
                longitude = event.message.longitude
                text_0 = "緯度 : {}, 経度 : {}\n".format(latitude, longitude)
                text_1 = "https://www.google.com/maps?q={},{}\n".format(latitude, longitude)
                messages = TextSendMessage(text= text_0 + text_1)
                line_bot_api.reply_message(event.reply_token, messages=messages)
            elif isinstance(event.message, TextMessage):
                logger.debug("Get Text Message")
                if event.message.text == "位置情報":
                    place = [QuickReplyButton(action=LocationAction(label="現在地を送信"))]
                    messages = TextSendMessage(text="📍現在地📍を送信してください", quick_reply=QuickReply(items=place))
                    line_bot_api.reply_message(event.reply_token, messages=messages)
                elif event.message.text == "カレンダー":
                    date_period = datetime.timedelta(days=7)
                    date_time_now = datetime.datetime.now()
                    date_time_min = date_time_now - date_period
                    date_time_max = date_time_now + date_period
                    messages = TemplateSendMessage(
                    alt_text='日付を選ぶ',
                    template=ButtonsTemplate(
                        text='日付を設定',
                        title='YYYY-MM-dd',
                        actions=[
                            DatetimePickerTemplateAction(
                            label='設定',
                            data='datetime-picker-action-postback',
                            mode='date',
                            initial = '{:04d}-{:02d}-{:02d}'.format(date_time_now.year, date_time_now.month, date_time_now.day),
                            min     = '{:04d}-{:02d}-{:02d}'.format(date_time_min.year, date_time_min.month, date_time_min.day),
                            max     = '{:04d}-{:02d}-{:02d}'.format(date_time_max.year, date_time_max.month, date_time_max.day)
                                )
                            ]
                        )
                    )
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