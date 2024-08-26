# bot/helpers.py

from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, URIAction, CarouselContainer, MessageAction

def send_books_carousel(event, books, line_bot_api, temporary_storage):
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
