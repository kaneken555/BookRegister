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
from linebot.models import CarouselContainer, URIAction


line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

# 一時的なストレージ
temporary_storage = {}

# ユーザーの状態を管理するためのストレージ
user_states = {}

# Example: 非同期で実行する関数
def perform_long_task(user_id, book_info):
    # 長時間かかる処理をここに記述
    save_book_info(book_info)  # データベースに保存する


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
        # ユーザーが検索モードかどうか確認
        if user_states.get(user_id) == "search_mode":
            # 検索モードの場合、入力されたメッセージを本のタイトルとして検索
            title_query = message_text
            books = search_books(title_query)
            
            # 検索結果が見つかったか確認
            if not books:
                send_response(event.reply_token, "該当する本が見つかりませんでした。別のタイトルを入力してください。")
            else:
                send_books_carousel(event, books)  # 複数の検索結果を表示
            
            user_states[user_id] = None  # 検索モードを解除
            send_push_quick_reply(user_id)  # 次の操作を促すクイックリプライを表示

        elif message_text == "検索":
            # 検索モードに変更
            user_states[user_id] = "search_mode"
            response = "検索したい本のタイトルを入力してください。"
            send_response(event.reply_token, response)

        elif message_text.startswith("register_"):
            title = message_text.split("_", 1)[1]  # タイトルを取得
            books = temporary_storage.get(user_id, [])
            book_info = next((book for book in books if book['title'].lower() == title.lower()), None)
            if book_info:
                perform_long_task(user_id, book_info)
                send_response(event.reply_token, f"Book '{book_info['title']}' has been saved.")
            else:
                send_response(event.reply_token, "Failed to register the book.")
            send_push_quick_reply(user_id)

        # elif message_text == "save book":  # 保存する場合
        #     book_info = temporary_storage.get(user_id)  # 保存された検索結果を取得
        #     if book_info:
        #         # 長時間の処理は別スレッドで実行
        #         threading.Thread(target=perform_long_task, args=(user_id, book_info)).start()
        #         response = "Your request is being processed."
        #     else:
        #         response = "No book information to save."
        #     send_response(event.reply_token, response)
        elif message_text == "list books":
            list_books(event)  # 登録中の本のリストを表示
            send_push_quick_reply(user_id)  # 次の操作を促すクイックリプライを表示
        elif message_text == "menu":  # クイックリプライを表示
            send_quick_reply(event)
        else:
            # 初回メッセージなどその他のメッセージはクイックリプライを表示
            send_quick_reply(event)

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
        QuickReplyButton(action=MessageAction(label="検索", text="検索")),
        QuickReplyButton(action=MessageAction(label="本リスト", text="list books")),
    ]
    
    quick_reply_message = TextSendMessage(
        text=quick_reply_text,
        quick_reply=QuickReply(items=quick_reply_buttons)
    )
    
    line_bot_api.reply_message(
        event.reply_token,
        quick_reply_message
    )

def send_push_quick_reply(user_id):
    quick_reply_text = "操作を選択してください:"
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="検索", text="検索")),
        QuickReplyButton(action=MessageAction(label="本リスト", text="list books"))
    ]
    
    quick_reply_message = TextSendMessage(
        text=quick_reply_text,
        quick_reply=QuickReply(items=quick_reply_buttons)
    )
    
    line_bot_api.push_message(
        user_id,
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
        return []
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return []

    # レスポンスのJSONデータをパース
    data = response.json()
    books = []

    if 'items' in data:
        for item in data['items']:
            book = item['volumeInfo']
            book_info = {
                'title': book.get('title', 'No title available'),
                'authors': ', '.join(book.get('authors', ['No authors available'])),
                'publisher': book.get('publisher', 'No publisher available'),
                'description': book.get('description', 'No description available'),
                'thumbnail': book.get('imageLinks', {}).get('thumbnail')  # サムネイル画像のURLを取得
            }
            books.append(book_info)

    return books

def send_books_carousel(event, books):
    bubbles = []
    
    for book in books:
        thumbnail_url = book['thumbnail'].replace("http://", "https://") if book['thumbnail'] else "https://via.placeholder.com/300x200.png?text=No+Image"

        bubble = BubbleContainer(
            hero=ImageComponent(
                url=thumbnail_url,
                size="full",
                aspect_ratio="20:13",
                aspect_mode="fit",
                action=URIAction(uri="https://line.me/")  # 適切なURLに変更
            ),
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text=book['title'], weight="bold", size="lg"),
                    BoxComponent(
                        layout="vertical",
                        margin="lg",
                        spacing="sm",
                        contents=[
                            BoxComponent(
                                layout="baseline",
                                spacing="sm",
                                contents=[
                                    TextComponent(text="著者", color="#aaaaaa", size="sm", flex=1),
                                    TextComponent(text=book['authors'], wrap=True, color="#666666", size="sm", flex=5)
                                ]
                            ),
                            BoxComponent(
                                layout="baseline",
                                spacing="sm",
                                contents=[
                                    TextComponent(text="概要", color="#aaaaaa", size="sm", flex=1),
                                    TextComponent(text=book['description'][:100] + "...", wrap=True, color="#666666", size="sm", flex=5)
                                ]
                            )
                        ]
                    )
                ]
            ),
            footer=BoxComponent(
                layout="vertical",
                spacing="sm",
                contents=[
                    ButtonComponent(
                        style="link",
                        height="sm",
                        action=MessageAction(label="登録", text=f"register_{book['title']}")
                    )
                ],
                flex=0
            )
        )
        bubbles.append(bubble)

    carousel = CarouselContainer(contents=bubbles)
    flex_message = FlexSendMessage(alt_text="Search results", contents=carousel)
    line_bot_api.reply_message(event.reply_token, flex_message)

    # 検索結果を一時的に保存しておく
    user_id = event.source.user_id
    temporary_storage[user_id] = books


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

# 登録中の本リストを表示
def list_books(event):
    books = Book.objects.all()  # すべての登録された本を取得
    
    if books.exists():
        bubbles = []
        
        for book in books:
            # URLがhttpの場合はhttpsに変換
            thumbnail_url = book.thumbnail if book.thumbnail else "https://via.placeholder.com/300x200.png?text=No+Image"
            thumbnail_url = thumbnail_url.replace("http://", "https://")

            bubble = BubbleContainer(
                hero=ImageComponent(
                    url=thumbnail_url,
                    size="full",
                    aspect_ratio="20:13",
                    aspect_mode="fit",
                    action=URIAction(uri="https://line.me/")
                ),
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(text=book.title, weight="bold", size="lg"),
                        BoxComponent(
                            layout="vertical",
                            margin="lg",
                            spacing="sm",
                            contents=[
                                BoxComponent(
                                    layout="baseline",
                                    spacing="sm",
                                    contents=[
                                        TextComponent(text="著者", color="#aaaaaa", size="sm", flex=1),
                                        TextComponent(text=book.authors, wrap=True, color="#666666", size="sm", flex=5)
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                footer=BoxComponent(
                    layout="vertical",
                    spacing="sm",
                    contents=[
                        ButtonComponent(
                            style="link",
                            height="sm",
                            action=URIAction(label="詳細", uri=f"https://example.com/books/{book.id}")
                        ),
                        ButtonComponent(
                            style="link",
                            height="sm",
                            action=URIAction(label="delete", uri="https://line.me/")
                        )
                    ],
                    flex=0
                )
            )
            bubbles.append(bubble)

        carousel = CarouselContainer(contents=bubbles)

        flex_message = FlexSendMessage(alt_text="Book list", contents=carousel)
        line_bot_api.reply_message(event.reply_token, flex_message)

    else:
        message = TextSendMessage(text="No books are currently registered.")
        line_bot_api.reply_message(event.reply_token, message)