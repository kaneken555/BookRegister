# bot/linebot_helpers.py

from linebot import LineBotApi
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
from linebot.exceptions import LineBotApiError

# メッセージを送信するヘルパー関数
def send_response(line_bot_api: LineBotApi, reply_token: str, message):
    try:
        # messageがFlexSendMessage/TextSendMessage/ImageSendMessageの場合
        if isinstance(message, (FlexSendMessage, TextSendMessage)):
            line_bot_api.reply_message(reply_token, message)
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
    except LineBotApiError as e:
        print(f"LineBotApiError (reply failed): {e.status_code}, {e.message}")

# クイックリプライを送信するヘルパー関数
def send_quick_reply(line_bot_api: LineBotApi, reply_token: str, text: str, quick_reply_buttons: list):
    quick_reply_message = TextSendMessage(
        text=text,
        quick_reply=QuickReply(items=quick_reply_buttons)
    )
    line_bot_api.reply_message(reply_token, quick_reply_message)

# クイックリプライのボタン作成ヘルパー関数
def create_quick_reply_button(label: str, text: str):
    return QuickReplyButton(action=MessageAction(label=label, text=text))

# プッシュ通知を送信するヘルパー関数
def send_push_quick_reply(line_bot_api: LineBotApi, user_id: str, text: str, quick_reply_buttons: list):
    quick_reply_message = TextSendMessage(
        text=text,
        quick_reply=QuickReply(items=quick_reply_buttons)
    )
    line_bot_api.push_message(user_id, quick_reply_message)
