from django.contrib import admin
from django.urls import path, include
import debug_toolbar
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

admin.site.site_header = "管理員後台"
admin.site.index_title = "Admin"

schema_view = get_schema_view(
    openapi.Info(
        title="ecommerce API",
        default_version="v1",
        description="Django Projects",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path(
        "",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("admin/", admin.site.urls),
    path("auth/", include("core.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("store/", include("store.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
]
