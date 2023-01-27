from rest_framework import generics, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from . import serializers


class UserCreated(generics.GenericAPIView):
    serializer_class = serializers.UserCreateSerializer

    @swagger_auto_schema(operation_summary="Create a user account by signing Up")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserMe(generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "patch"]
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        return {"request": self.request}

    @swagger_auto_schema(operation_summary="View personal account information")
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Change personal account information")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
