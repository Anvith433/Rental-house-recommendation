from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """``?page=1&page_size=20``; page size is capped to protect the database."""

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50
