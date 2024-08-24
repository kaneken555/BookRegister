# bot/database_helpers.py

from .models import Book

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
