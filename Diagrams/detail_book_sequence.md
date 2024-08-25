```mermaid
sequenceDiagram
    participant User
    participant Views
    participant Handlers
    participant Databasehelpers
    participant LineBotHelpers

    User->>Views: 本の詳細を表示する
    Views->>Handlers: handle_detail()
    Handlers->>Databasehelpers: detail_book()(未実装)
    Databasehelpers-->>Handlers: bookinfoを返す(未実装)
    Handlers->>LineBotHelpers: send_response(結果)
    LineBotHelpers-->>User: 結果を送信