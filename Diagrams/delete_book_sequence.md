```mermaid
sequenceDiagram
    participant User
    participant Views
    participant Handlers
    participant Databasehelpers
    participant LineBotHelpers

    User->>Views: 本を削除する
    Views->>Handlers: handle_delete_book()
    Handlers->>Databasehelpers: delete_book_by_id()
    Databasehelpers-->>Handlers: 結果を返す
    Handlers->>LineBotHelpers: send_response(結果)
    LineBotHelpers-->>User: 結果を送信