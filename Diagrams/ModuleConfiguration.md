```mermaid
classDiagram
    class Views {
        +handle_message()
        +callback()
        +perform_long_task()   
    }

    class Handlers {
        +handle_search_mode()
        +handle_register()
        +handle_list_books()
        +handle_default()
        +handle_delete_book()
    }

    class LineBotHelpers {
        +send_response()
        +send_quick_reply()
        +send_push_quick_reply()
        +create_quick_reply_button()
    }

    class Search {
        +search_books()
    }

    class Helpers {
        +send_books_carousel()
    }

    class DatabaseHelpers {
        +save_book_info()
        +list_books()
        +delete_book_by_id()
    }

    Views --> Handlers : uses
    Views --> LineBotHelpers : uses
    Views --> Search : uses
    Views --> Helpers : uses
    Views --> DatabaseHelpers : uses

    Handlers --> LineBotHelpers : uses
    Handlers --> DatabaseHelpers : uses
