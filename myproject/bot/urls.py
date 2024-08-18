# bot/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('callback/', views.callback, name='callback'),
    # path('', views.user_books, name='user_books'),  # トップページとして設定
    # path('line/login/', views.line_login, name='line_login'),
    # path('line/callback/', views.line_callback, name='line_callback'),
]
