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
from .search import search_books  # search_books 関数をインポート
from .linebot_helpers import send_response, send_quick_reply, send_push_quick_reply, create_quick_reply_button, send_book_info_with_thumbnail
from .handlers import handle_search_mode, handle_register, handle_list_books, handle_default
from .helpers import send_books_carousel  # helpersからインポート
from .database_helpers import save_book_info




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
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        return HttpResponse(status=400)  # 署名がない場合は 400 を返す

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
            handle_search_mode(event, user_id, message_text, user_states, temporary_storage, line_bot_api)

            # # 検索モードの場合、入力されたメッセージを本のタイトルとして検索
            # title_query = message_text
            # books = search_books(title_query)
            
            # # 検索結果が見つかったか確認
            # if not books:
            #     send_response(line_bot_api, event.reply_token, "該当する本が見つかりませんでした。別のタイトルを入力してください。")
            # else:
            #     send_books_carousel(event, books)  # 複数の検索結果を表示
            
            # user_states[user_id] = None  # 検索モードを解除
            # # send_push_quick_reply(user_id)  # 次の操作を促すクイックリプライを表示
            # send_push_quick_reply(line_bot_api, user_id, "次の操作を選択してください:", [
            #     create_quick_reply_button("検索", "検索"),
            #     create_quick_reply_button("本リスト", "list books")
            # ])

        elif message_text == "検索":
            # 検索モードに変更
            user_states[user_id] = "search_mode"
            response = "検索したい本のタイトルを入力してください。"
            send_response(line_bot_api, event.reply_token, response)

        elif message_text.startswith("register_"):
            handle_register(event, user_id, message_text, temporary_storage, line_bot_api)

            # title = message_text.split("_", 1)[1]  # タイトルを取得
            # books = temporary_storage.get(user_id, [])
            # book_info = next((book for book in books if book['title'].lower() == title.lower()), None)
            # if book_info:
            #     perform_long_task(user_id, book_info)
            #     send_response(line_bot_api, event.reply_token, f"Book '{book_info['title']}' has been saved.")
            # else:
            #     send_response(line_bot_api, event.reply_token, "Failed to register the book.")
            # # send_push_quick_reply(user_id)
            # send_push_quick_reply(line_bot_api, user_id, "次の操作を選択してください:", [
            #     create_quick_reply_button("検索", "検索"),
            #     create_quick_reply_button("本リスト", "list books")
            # ])

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
            handle_list_books(event, line_bot_api)

            # list_books(event)  # 登録中の本のリストを表示
            # # send_push_quick_reply(user_id)  # 次の操作を促すクイックリプライを表示
            # send_push_quick_reply(line_bot_api, user_id, "次の操作を選択してください:", [
            #     create_quick_reply_button("検索", "検索"),
            #     create_quick_reply_button("本リスト", "list books")
            # ])
        else:
            # 初回メッセージなどその他のメッセージはクイックリプライを表示
            # send_quick_reply(event)
            handle_default(event, line_bot_api)


    except LineBotApiError as e:
        print(f"LineBotApiError: {e.status_code}, {e.message}")
        for detail in e.error.details:
            print(f"  {detail.property}: {detail.message}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



# def send_quick_reply(event):
#     quick_reply_text = "Please select an option:"
#     quick_reply_buttons = [
#         QuickReplyButton(action=MessageAction(label="検索", text="検索")),
#         QuickReplyButton(action=MessageAction(label="本リスト", text="list books")),
#     ]
    
#     quick_reply_message = TextSendMessage(
#         text=quick_reply_text,
#         quick_reply=QuickReply(items=quick_reply_buttons)
#     )
    
#     line_bot_api.reply_message(
#         event.reply_token,
#         quick_reply_message
#     )

# def send_push_quick_reply(user_id):
#     quick_reply_text = "操作を選択してください:"
#     quick_reply_buttons = [
#         QuickReplyButton(action=MessageAction(label="検索", text="検索")),
#         QuickReplyButton(action=MessageAction(label="本リスト", text="list books"))
#     ]
    
#     quick_reply_message = TextSendMessage(
#         text=quick_reply_text,
#         quick_reply=QuickReply(items=quick_reply_buttons)
#     )
    
#     line_bot_api.push_message(
#         user_id,
#         quick_reply_message
#     )
