# search.py

import requests
from django.conf import settings

def search_books(title):
    api_key = settings.GOOGLE_BOOKS_API_KEY
    url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}&key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []
    # レスポンスのJSONデータをパース
    data = response.json()
    books = []
    if 'items' in data:
        for item in data['items']:
            book = item['volumeInfo']
            book_info = {
                'title': book.get('title', 'No title available'),
                'authors': ', '.join(book.get('authors', ['No authors available'])),
                'publisher': book.get('publisher', 'No publisher available'),
                'description': book.get('description', 'No description available'),
                'thumbnail': book.get('imageLinks', {}).get('thumbnail')
            }
            books.append(book_info)
    return books
