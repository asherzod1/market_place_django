from rest_framework import pagination


class CustomPagination(pagination.PageNumberPagination):
    page_size = 10  # Set the number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100