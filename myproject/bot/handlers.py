# bot/handlers.py

from .linebot_helpers import send_response, send_quick_reply, send_push_quick_reply, create_quick_reply_button
from .search import search_books
from .helpers import send_books_carousel  # helpersからsend_books_carousel関数をインポート

from .models import Book
from linebot.models import BubbleContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, CarouselContainer, FlexSendMessage, TextSendMessage
from linebot.models.actions import URIAction, MessageAction
from .database_helpers import save_book_info, delete_book_by_id


def handle_search_mode(event, user_id, message_text, user_states, temporary_storage, line_bot_api):
    title_query = message_text
    books = search_books(title_query)

    if not books:
        send_response(line_bot_api, event.reply_token, "該当する本が見つかりませんでした。別のタイトルを入力してください。")
    else:
        send_books_carousel(event, books, line_bot_api, temporary_storage)

    user_states[user_id] = None
    send_push_quick_reply(line_bot_api, user_id, "次の操作を選択してください:", [
        create_quick_reply_button("検索", "検索"),
        create_quick_reply_button("本リスト", "list books")
    ])

def handle_register(event, user_id, message_text, temporary_storage, line_bot_api):
    title = message_text.split("_", 1)[1]
    books = temporary_storage.get(user_id, [])
    book_info = next((book for book in books if book['title'].lower() == title.lower()), None)
    if book_info:
        perform_long_task(user_id, book_info, line_bot_api)
        send_response(line_bot_api, event.reply_token, f"Book '{book_info['title']}' has been saved.")
    else:
        send_response(line_bot_api, event.reply_token, "Failed to register the book.")
    send_push_quick_reply(line_bot_api, user_id, "次の操作を選択してください:", [
        create_quick_reply_button("検索", "検索"),
        create_quick_reply_button("本リスト", "list books")
    ])

def handle_list_books(event, line_bot_api):
    list_books(event, line_bot_api)  # list_books関数を呼び出す
    send_push_quick_reply(line_bot_api, event.source.user_id, "次の操作を選択してください:", [
        create_quick_reply_button("検索", "検索"),
        create_quick_reply_button("本リスト", "list books")
    ])

def handle_default(event, line_bot_api):
    quick_reply_text = "Please select an option:"
    quick_reply_buttons = [
        create_quick_reply_button("検索", "検索"),
        create_quick_reply_button("本リスト", "list books"),
    ]
    
    send_quick_reply(
        line_bot_api=line_bot_api,
        reply_token=event.reply_token,
        text=quick_reply_text,
        quick_reply_buttons=quick_reply_buttons
    )


def handle_delete_book(event, user_id, message_text, line_bot_api):
    """
    本の削除を処理する
    """
    book_id = message_text.split("_", 1)[1]  # IDを取得
    success = delete_book_by_id(book_id)
    if success:
        response = f"Book with ID {book_id} has been deleted."
    else:
        response = f"Book with ID {book_id} could not be found."
    send_response(line_bot_api, event.reply_token, response)

    # 次の操作を促すクイックリプライを送信
    send_push_quick_reply(line_bot_api, user_id, "次の操作を選択してください:", [
        create_quick_reply_button("検索", "検索"),
        create_quick_reply_button("本リスト", "list books")
    ])


def perform_long_task(user_id, book_info, line_bot_api):
    save_book_info(book_info)  # データベースに保存する


# 登録中の本リストを表示
def list_books(event, line_bot_api):
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
                            action=MessageAction(label="delete", text=f"delete_{book.id}")
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