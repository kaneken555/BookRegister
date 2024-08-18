# bot/views.py

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from linebot.models import ImageSendMessage, FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, ImageComponent, ButtonComponent, SeparatorComponent
import requests
from .models import Book
import threading  # 非同期処理のためのモジュール


line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

# 一時的なストレージ
temporary_storage = {}


# Example: 非同期で実行する関数
def perform_long_task(user_id, book_info):
    # 長時間かかる処理をここに記述
    result = save_book_info(book_info)  # データベースに保存する
    # 結果をユーザーに送信（プッシュメッセージ）
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=f"Book information saved: {result['title']}")
    )

@csrf_exempt
def callback(request):
    signature = request.headers['X-Line-Signature']
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature error")
        return HttpResponse(status=403)
    except Exception as e:
        print(f"An error occurred: {e}")
        return HttpResponse(status=500)

    return HttpResponse(status=200)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_text = event.message.text.strip().lower()
    user_id = event.source.user_id  # ユーザーIDを取得

    try:
        if message_text.startswith("book "):  # 'book 'で始まるメッセージに対してGoogle Books APIを使用
            title_query = message_text.split(" ", 1)[1]
            book_info = search_books(title_query)
            temporary_storage[user_id] = book_info  # 検索結果を一時的に保存
            send_book_info_with_thumbnail(event, book_info)
        elif message_text == "save book":  # 保存する場合
            book_info = temporary_storage.get(user_id)  # 保存された検索結果を取得
            if book_info:
                # 長時間の処理は別スレッドで実行
                threading.Thread(target=perform_long_task, args=(user_id, book_info)).start()
                response = "Your request is being processed."
            else:
                response = "No book information to save."
            send_response(event.reply_token, response)
        elif message_text == "menu":  # クイックリプライを表示
            send_quick_reply(event)
        else:
            response = f"You said: {event.message.text}"
            send_response(event.reply_token, response)

    except LineBotApiError as e:
        print(f"LineBotApiError: {e.status_code}, {e.message}")
        for detail in e.error.details:
            print(f"  {detail.property}: {detail.message}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def send_response(reply_token, message):
    try:
        # messageがFlexSendMessage/TextSendMessage/ImageSendMessageの場合
        if isinstance(message, (FlexSendMessage, TextSendMessage, ImageSendMessage)):
            line_bot_api.reply_message(reply_token, message)
        # それ以外のケースがあれば、それを考慮して処理する
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
    except LineBotApiError as e:
        print(f"LineBotApiError (reply failed): {e.status_code}, {e.message}")


def send_quick_reply(event):
    quick_reply_text = "Please select an option:"
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="View Tasks", text="tasklist")),
        QuickReplyButton(action=MessageAction(label="テクノロジーのニュース", text="news technology"))
    ]
    
    quick_reply_message = TextSendMessage(
        text=quick_reply_text,
        quick_reply=QuickReply(items=quick_reply_buttons)
    )
    
    line_bot_api.reply_message(
        event.reply_token,
        quick_reply_message
    )
    

def send_book_info_with_thumbnail(event, book_info):
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
        send_response(event.reply_token, book_text)


def search_books(title):
    api_key = settings.GOOGLE_BOOKS_API_KEY
    url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}&key={api_key}"

    try:
        # APIリクエストを実行し、ステータスコードが200以外の場合は例外を発生させる
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return {
            'title': 'Failed to fetch book information due to an HTTP error.',
            'authors': '',
            'publisher': '',
            'description': '',
            'thumbnail': None
        }
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return {
            'title': 'Failed to fetch book information due to a request error.',
            'authors': '',
            'publisher': '',
            'description': '',
            'thumbnail': None
        }

    # レスポンスのJSONデータをパース
    data = response.json()

    if 'items' in data and data['items']:
        book = data['items'][0]['volumeInfo']
        book_info = {
            'title': book.get('title', 'No title available'),
            'authors': ', '.join(book.get('authors', ['No authors available'])),
            'publisher': book.get('publisher', 'No publisher available'),
            'description': book.get('description', 'No description available'),
            'thumbnail': book.get('imageLinks', {}).get('thumbnail')  # サムネイル画像のURLを取得
        }
    else:
        book_info = {
            'title': 'No books found for your query.',
            'authors': '',
            'publisher': '',
            'description': '',
            'thumbnail': None
        }

    return book_info


def save_book_info(book_info):
    title = book_info.get('title', 'No title available')
    authors = book_info.get('authors', 'No authors available')
    publisher = book_info.get('publisher', 'No publisher available')
    description = book_info.get('description', 'No description available')
    thumbnail = book_info.get('thumbnail', 'No thumnail available')  # サムネイルURLを取得

    # Bookモデルに保存
    book = Book.objects.create(
        title=title,
        authors=authors,
        publisher=publisher,
        description=description,
        thumbnail=thumbnail  # サムネイルURLを保存

    )

    # 保存した本の情報を返す
    return {
        'title': book.title,
        'authors': book.authors,
        'publisher': book.publisher,
        'description': book.description
    }

