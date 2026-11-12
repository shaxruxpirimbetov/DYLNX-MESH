from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle


class StaffExemptUserRateThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_staff:
            return True
        return super().allow_request(request, view)


class FlexiblePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 500