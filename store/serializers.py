from asyncore import read
from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from . import models
from .signals import order_created


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Collection
        fields = ["id", "title", "featured_product", "product_count"]

    product_count = serializers.IntegerField(read_only=True)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImage
        fields = ["image"]

    def create(self, validated_data):
        product_id = self.context["product_id"]

        return models.ProductImage.objects.create(
            product_id=product_id, **validated_data
        )


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.Product
        fields = [
            "id",
            "title",
            "description",
            "price",
            "slug",
            "inventory",
            "images",
            "collection",
            "price_with_tax",
        ]

    price_with_tax = serializers.SerializerMethodField(method_name="calculate_tax")

    def calculate_tax(self, product):
        return product.price * Decimal(1.1)


class CustomerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = ["first_name", "last_name"]


class ReviewCustomerSerializer(serializers.ModelSerializer):
    user = CustomerUserSerializer()

    class Meta:
        model = models.Customer
        fields = ["id", "user", "membership"]


class ReviewSerializer(serializers.ModelSerializer):
    customer = ReviewCustomerSerializer(read_only=True)

    class Meta:
        model = models.Review
        fields = ["id", "date", "customer", "description"]

    def create(self, validated_data):
        product_id = self.context["product_id"]
        user_id = self.context["user_id"]
        if (
            models.Review.objects.select_related("customer")
            .filter(customer_id=user_id, product_id=product_id)
            .exists()
        ):
            raise serializers.ValidationError("you have already commented.")
        else:
            return models.Review.objects.create(
                customer_id=user_id, product_id=product_id, **validated_data
            )


class ItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = ["id", "title", "price"]


class CartItemSerializer(serializers.ModelSerializer):
    product = ItemProductSerializer()
    subtotal = serializers.SerializerMethodField(method_name="cal_subtotal")

    def cal_subtotal(self, cartItem):
        return cartItem.quantity * cartItem.product.price

    class Meta:
        model = models.CartItem
        fields = ["id", "product", "quantity", "subtotal"]


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    cart_items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name="cal_total_price")

    def cal_total_price(self, cart):
        return sum(
            [item.quantity * item.product.price for item in cart.cart_items.all()]
        )

    class Meta:
        model = models.Cart
        fields = ["id", "cart_items", "total_price"]


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    product = ItemProductSerializer(read_only=True)

    def validate_product_id(self, value):
        if not models.Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No product with the given ID was found.")
        return value

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        product_id = self.validated_data["product_id"]
        quantity = self.validated_data["quantity"]

        try:
            cart_item = models.CartItem.objects.get(
                cart_id=cart_id, product_id=product_id
            )
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except models.CartItem.DoesNotExist:
            self.instance = models.CartItem.objects.create(
                cart_id=cart_id, **self.validated_data
            )

        return self.instance

    class Meta:
        model = models.CartItem
        fields = ["id", "product_id", "product", "quantity"]


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = ["quantity"]


class CustomerSerializer(serializers.ModelSerializer):
    membership = serializers.CharField(read_only=True)

    class Meta:
        model = models.Customer
        fields = [
            "id",
            "user_id",
            "first_name",
            "last_name",
            "birth_date",
            "membership",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ItemProductSerializer()

    class Meta:
        model = models.OrderItem
        fields = ["id", "product", "unit_price", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = models.Order
        fields = ["id", "customer", "placed_at", "payment_status", "order_items"]


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = ["payment_status"]


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not models.Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError("No cart with the given ID was found.")
        if models.CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError("The cart is empty.")
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data["cart_id"]

            customer = models.Customer.objects.get(user_id=self.context["user_id"])
            order = models.Order.objects.create(customer=customer)

            cart_items = models.CartItem.objects.select_related("product").filter(
                cart_id=cart_id
            )
            order_items = [
                models.OrderItem(
                    order=order,
                    product=item.product,
                    unit_price=item.product.price,
                    quantity=item.quantity,
                )
                for item in cart_items
            ]
            models.OrderItem.objects.bulk_create(order_items)
            models.Cart.objects.filter(pk=cart_id).delete()
            order_created.send_robust(self.__class__, order=order)
            return order
