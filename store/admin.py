from django.contrib import admin, messages
from django.db.models import Count
from django.utils.html import format_html, urlencode
from django.urls import reverse
from . import models
from tag.admin import TagInline


class InventoryFilter(admin.SimpleListFilter):
    title = "inventory"
    parameter_name = "inventory"

    def lookups(self, request, model_admin):
        return [
            ("<10", "庫存緊張"),
            (">=10", "庫存充裕"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "<10":
            return queryset.filter(inventory__lt=10)
        else:
            return queryset.filter(inventory__gt=10)


class ProductImageInline(admin.TabularInline):
    model = models.ProductImage
    readonly_fields = ["thumbnail"]

    def thumbnail(self, instance):
        if instance.image.name != "":
            return format_html(f'<img src="{instance.image.url}" class = "thumbnail"/>')
        return ""


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "price",
        "inventory_status",
        "collection_title",
    ]
    prepopulated_fields = {"slug": ["title"]}
    list_editable = ["price"]
    list_per_page = 10
    list_select_related = ["collection"]
    list_filter = ("last_update", "collection", InventoryFilter)
    search_fields = ["title__istartswith"]
    inlines = [ProductImageInline, TagInline]

    @admin.display(ordering="inventory")
    def inventory_status(self, product):
        if product.inventory < 10:
            return "庫存緊張"
        return "庫存充裕"

    def collection_title(self, product):
        return product.collection.title

    @admin.action(description="Clear inventory")
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f"{updated_count} products were successfully updated.",
            messages.ERROR,
        )

    class Media:
        css = {"all": ["store/styles.css"]}


class AddressInline(admin.TabularInline):
    model = models.Address
    min_num = 1
    max_num = 10
    extra = 0


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["user", "first_name", "last_name", "membership", "order_count"]
    list_editable = ["membership"]
    list_per_page = 10
    list_select_related = ["user"]
    search_fields = [
        "user__username__istartswith",
        "first_name__istartswith",
        "last_name__istartswith",
    ]
    search_help_text = "你可以查找用戶姓名"
    inlines = [AddressInline]

    @admin.display(ordering="order_count")
    def order_count(self, customer):
        url = (
            reverse("admin:store_order_changelist")
            + "?"
            + urlencode({"customer__id": str(customer.id)})
        )
        return format_html('<a href="{}">{}</a>', url, f"{customer.order_count}筆")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(order_count=Count("order"))


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["title", "featured_product", "product_count"]
    list_editable = ["featured_product"]
    autocomplete_fields = ["featured_product"]
    list_per_page = 10
    search_fields = ["title__istartswith"]
    search_help_text = "你可以查找商品分類"
    ordering = ["title"]

    @admin.display(ordering="product_count")
    def product_count(self, collection):
        url = (
            reverse("admin:store_product_changelist")
            + "?"
            + urlencode({"collection__id": str(collection.id)})
        )
        return format_html('<a href="{}">{}</a>', url, f"{collection.product_count}個")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count("product"))


class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    autocomplete_fields = ["product"]
    min_num = 1
    max_num = 10
    extra = 0


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "placed_at", "payment_status", "customer"]
    list_editable = ["payment_status"]
    list_per_page = 10
    ordering = ["payment_status"]
    autocomplete_fields = ["customer"]
    inlines = [OrderItemInline]
