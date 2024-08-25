# bot/database_helpers.py

from .models import Book
from linebot.models import BubbleContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, CarouselContainer, FlexSendMessage, TextSendMessage
from linebot.models.actions import URIAction, MessageAction

def save_book_info(book_info):
    title = book_info.get('title', 'No title available')
    authors = book_info.get('authors', 'No authors available')
    publisher = book_info.get('publisher', 'No publisher available')
    description = book_info.get('description', 'No description available')
    thumbnail = book_info.get('thumbnail', 'No thumbnail available')

    book = Book.objects.create(
        title=title,
        authors=authors,
        publisher=publisher,
        description=description,
        thumbnail=thumbnail
    )

    return {
        'title': book.title,
        'authors': book.authors,
        'publisher': book.publisher,
        'description': book.description
    }

def delete_book_by_id(book_id):
    """
    指定されたIDの本をデータベースから削除する
    """
    try:
        book = Book.objects.get(id=book_id)
        book.delete()
        return True
    except Book.DoesNotExist:
        return False


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
