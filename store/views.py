from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    UpdateModelMixin,
)
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from . import models, serializers
from .pagination import DefaultPagination
from .filter import ProductFilter
from .permissions import IsAdminOrReadOnly, OwnerOrAdmin


class CollectionViewSet(ModelViewSet):
    queryset = models.Collection.objects.annotate(product_count=Count("product"))
    serializer_class = serializers.CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        collection = models.Collection.objects.get(pk=kwargs["pk"])
        if collection.product.all().count() > 0:
            return Response(
                {
                    "error": "Collection can't be deleted because it's associated with product"
                },
            )
        return super().destroy(request, *args, **kwargs)


class ProductViewSet(ModelViewSet):
    queryset = models.Product.objects.prefetch_related("images").all()
    serializer_class = serializers.ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "description", "collection__title"]
    ordering_fields = ["price", "last_update"]
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if models.OrderItem.objects.filter(product_id=kwargs["pk"]).count() > 0:
            return Response(
                {
                    "error": "Product can't be deleted because it's associated with orderitem"
                },
            )
        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = serializers.ReviewSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return {}
        else:
            return models.Review.objects.select_related("product").filter(
                product_id=self.kwargs["products_pk"]
            )

    def get_permissions(self):
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [OwnerOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def get_serializer_context(self):
        if getattr(self, "swagger_fake_view", False):
            return {}
        else:
            return {
                "product_id": self.kwargs["products_pk"],
                "user_id": self.request.user.id,
            }


class ProductImageViewSet(ModelViewSet):
    serializer_class = serializers.ProductImageSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return {}
        else:
            return models.ProductImage.objects.select_related("product").filter(
                product_id=self.kwargs["products_pk"]
            )

    def get_serializer_context(self):
        if getattr(self, "swagger_fake_view", False):
            return {}
        else:
            return {
                "product_id": self.kwargs["products_pk"],
            }


class CartViewSet(
    CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet
):
    queryset = models.Cart.objects.prefetch_related("cart_items").all()
    serializer_class = serializers.CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.AddCartItemSerializer
        elif self.request.method == "PATCH":
            return serializers.UpdateCartItemSerializer
        return serializers.CartItemSerializer

    def get_serializer_context(self):
        if getattr(self, "swagger_fake_view", False):
            return {}
        else:
            return {"cart_id": self.kwargs["carts_pk"]}

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return {}
        else:
            return models.CartItem.objects.filter(
                cart_id=self.kwargs["carts_pk"]
            ).select_related("product")


class CustomerViewSet(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    queryset = models.Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["GET", "PUT"], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = models.Customer.objects.get(user_id=request.user.id)
        if request.method == "GET":
            serializer = serializers.CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = serializers.CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [OwnerOrAdmin()]
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = serializers.CreateOrderSerializer(
            data=request.data, context={"user_id": self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = serializers.OrderSerializer(order)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.CreateOrderSerializer
        elif self.request.method == "PATCH":
            return serializers.UpdateOrderSerializer
        return serializers.OrderSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return {}
        else:
            user = self.request.user
            if user.is_staff:
                return models.Order.objects.all()
            customer_id = models.Customer.objects.only("id").get(user_id=user.id)
            return models.Order.objects.filter(customer_id=customer_id)
