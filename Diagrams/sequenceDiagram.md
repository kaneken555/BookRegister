```mermaid
sequenceDiagram
    participant User
    participant Views
    participant Handlers
    participant Search
    participant LineBotHelpers
    
    User->>Views: 本を検索する
    Views->>Handlers: handle_search_mode()
    Handlers->>Search: search_books()
    Search-->>Handlers: 検索結果を返す
    Handlers->>LineBotHelpers: send_response(検索結果)
    LineBotHelpers-->>User: 検索結果を送信
