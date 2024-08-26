```mermaid
sequenceDiagram
    participant User
    participant Views
    participant Handlers
    participant Databasehelpers
    participant LineBotHelpers

    User->>Views: 本を登録する
    Views->>Handlers: handle_register()
    Handlers->>Databasehelpers: save_book_info()
    Databasehelpers-->>Handlers: bookinfoを返す
    Handlers->>LineBotHelpers: send_response(結果)
    LineBotHelpers-->>User: 結果を送信