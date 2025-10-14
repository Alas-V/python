from models import AdminPermission


class PermissionChecker:
    @staticmethod
    def has_permission(
        user_permissions: int, required_permission: AdminPermission
    ) -> bool:
        return bool(user_permissions & required_permission)

    @staticmethod
    def get_accessible_sections(user_permissions: int) -> dict:
        return {
            "stats": PermissionChecker.has_permission(
                user_permissions, AdminPermission.VIEW_STATS
            ),
            "orders": PermissionChecker.has_permission(
                user_permissions, AdminPermission.MANAGE_ORDERS
            ),
            "books": PermissionChecker.has_permission(
                user_permissions, AdminPermission.MANAGE_BOOKS
            ),
            "admins": PermissionChecker.has_permission(
                user_permissions, AdminPermission.MANAGE_ADMINS
            ),
            "support": PermissionChecker.has_permission(
                user_permissions, AdminPermission.MANAGE_SUPPORT
            ),
            "super_admin": PermissionChecker.has_permission(
                user_permissions, AdminPermission.SUPER_ADMIN_PERMS
            ),
        }
