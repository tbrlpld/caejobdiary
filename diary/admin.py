from django.contrib import admin

from .models import Job, Keyword, Tag

# Register your models here.
admin.site.register(Job)
admin.site.register(Keyword)
admin.site.register(Tag)
