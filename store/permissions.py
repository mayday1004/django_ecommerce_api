from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # 安全方法(GET,OPTION,HEAD)
            return True
        return bool(request.user and request.user.is_staff)


class OwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(obj.customer.user == request.user or request.user.is_staff)
