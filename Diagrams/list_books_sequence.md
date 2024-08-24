```mermaid
sequenceDiagram
    participant User
    participant Views
    participant Handlers
    participant Databasehelpers
    participant LineBotHelpers

    User->>Views: 本リストを表示する
    Views->>Handlers: handle_list_books()
    Handlers->>Databasehelpers: list_books()
    Databasehelpers-->>Handlers: 検索結果を返す(未実装)
    Handlers->>LineBotHelpers: send_response(検索結果)(不明)
    LineBotHelpers-->>User: 検索結果を送信(不明)