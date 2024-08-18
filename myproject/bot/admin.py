from django.contrib import admin
from .models import Task, Book

admin.site.register(Task)
admin.site.register(Book)