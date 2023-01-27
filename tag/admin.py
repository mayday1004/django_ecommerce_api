from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from . import models


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["label__istartswith"]


class TagInline(GenericTabularInline):
    model = models.TaggedItem
    autocomplete_fields = ["tag"]
    extra = 1
