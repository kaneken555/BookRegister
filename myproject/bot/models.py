from django.db import models

from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)  # ユーザーと本を関連付けるフィールド
    google_books_id = models.CharField(max_length=255, unique=True)  # Google Books APIから取得した本のID
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)    
    thumbnail = models.URLField(max_length=500, blank=True, null=True)  # サムネイルURLのフィールドを追加
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title