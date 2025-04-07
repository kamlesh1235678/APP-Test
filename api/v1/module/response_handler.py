from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import json
from rest_framework.pagination import PageNumberPagination
import math

def response_handler(message,code,data,error_message="",extra={}):
	return Response({"message":message, "code":code, 'data':data,'error_message':error_message,'extra':extra} , status= code)

def serialiser_errors(serializer):
	error_message = " & ".join([str(serializer.errors.get(error)[0]) for error in serializer.errors])
	return error_message

class CustomPagination(PageNumberPagination):
	page_size =10
	max_page_size = 1000
	page_size_query_param = 'page_size'
	def get_paginated_response(self, data):
		if self.request.query_params.get('page_size'):
			self.page_size = int(self.request.query_params.get('page_size'))

		total_page = math.ceil(self.page.paginator.count / self.page_size)
		return Response({
				'count': self.page.paginator.count,
				'total': total_page,
				'page_size': self.page_size,
				'current': self.page.number,
				'previous': self.get_previous_link(),
				'next': self.get_next_link(),
				'data': data,
				'message':'fetch'
        })
      

def format_serializer_errors(errors):
    """
    Converts serializer errors into a list of formatted error messages.
    """
    error_list = []
    for field, error_messages in errors.items():
        for error in error_messages:
            error_list.append(f"{field}: {str(error)}")  # Format as 'field: error message'
    return error_list


def format_serializer_errors_nested(errors):
    def parse_errors(errors, parent_key=""):
        error_list = []
        for field, error_messages in errors.items():
            field_name = f"{field}" if parent_key else field  # Handle nested fields
            if isinstance(error_messages, dict):  # Handle nested errors
                error_list.extend(parse_errors(error_messages, field_name))
            elif isinstance(error_messages, list):  # Handle list of errors
                for error in error_messages:
                    error_list.append(f"{field_name}: {str(error)}")
        return error_list

    return parse_errors(errors)
