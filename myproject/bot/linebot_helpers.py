# bot/linebot_helpers.py

from linebot import LineBotApi
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
from linebot.exceptions import LineBotApiError
from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, SeparatorComponent, MessageAction

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


# 書籍の情報をサムネイル付きのFlexメッセージとして送信する
def send_book_info_with_thumbnail(line_bot_api, event, book_info):
    if book_info['thumbnail']:
        # HTTPS URL に変換
        thumbnail_url = book_info['thumbnail'].replace("http://", "https://")

        # Flex Messageでサムネイル画像付きのメッセージを送信
        flex_message = FlexSendMessage(
            alt_text="Book information",
            contents=BubbleContainer(
                direction="ltr",
                hero=ImageComponent(
                    url=thumbnail_url,
                    size="full",
                    aspect_ratio="4:3",
                    aspect_mode="fit"
                ),
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(text=f"Title: {book_info['title']}", weight="bold", size="lg", wrap=True),
                        TextComponent(text=f"Authors: {book_info['authors']}", size="sm", wrap=True),
                        TextComponent(text=f"Publisher: {book_info['publisher']}", size="sm", wrap=True),
                        SeparatorComponent(margin="md"),
                        TextComponent(text=f"Description: {book_info['description'][:300]}...", size="sm", wrap=True)
                    ]
                ),
                footer=BoxComponent(
                    layout="vertical",
                    contents=[
                        ButtonComponent(
                            style="link",
                            height="sm",
                            action=MessageAction(label="Save Book", text="save book")
                        )
                    ]
                )
            )
        )

        try:
            line_bot_api.reply_message(
                event.reply_token,
                flex_message
            )
        except LineBotApiError as e:
            print(f"LineBotApiError (flex reply failed): {e.status_code}, {e.message}")
            print(f"Flex Message: {flex_message}")
    else:
        # サムネイルがない場合は通常のテキストメッセージを送信
        book_text = (
            f"Title: {book_info['title']}\n"
            f"Authors: {book_info['authors']}\n"
            f"Publisher: {book_info['publisher']}\n"
            f"Description: {book_info['description']}"
        )
        send_response(line_bot_api, event.reply_token, book_text)