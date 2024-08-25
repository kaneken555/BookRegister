# bot/database_helpers.py

from .models import Book

def save_book_info(book_info):
    google_books_id = book_info.get('google_books_id')
    title = book_info.get('title', 'No title available')
    authors = book_info.get('authors', 'No authors available')
    publisher = book_info.get('publisher', 'No publisher available')
    description = book_info.get('description', 'No description available')
    thumbnail = book_info.get('thumbnail', 'No thumbnail available')

    # google_books_idで既存の本を取得し、なければ新しく作成する
    book, created = Book.objects.get_or_create(
        google_books_id=google_books_id,
        defaults={
            'title': title,
            'authors': authors,
            'publisher': publisher,
            'description': description,
            'thumbnail': thumbnail,
        }
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
