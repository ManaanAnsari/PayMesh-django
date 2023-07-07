from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class GlobalPagination(PageNumberPagination):
    '''
    this pagination 'll be used everywhere to keep everything consistent
    '''
    def get_paginated_response(self, data):
        return Response({
            'page_details': {
                'next': self.page.next_page_number() if self.page.has_next() else None,
                'previous': self.page.previous_page_number() if self.page.has_previous() else None,
                'count': self.page.paginator.count,
                'page_size': self.page_size,
            },
            'data': data
        })