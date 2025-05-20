from rest_framework import viewsets
from modules.administration.models import *
from api.v1.module.serializers.leave_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from api.v1.module.response_handler import *
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError , NotFound


class StudentLeaveRequestPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'StudentLeaveRequest no found' , 'code':400 , 'data': [] , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "StudentLeaveRequest list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class StudentLeaveRequestModelViewSet(viewsets.ModelViewSet):
    queryset = StudentLeaveRequest.objects.all().order_by('-id')
    serializer_class = StudentLeaveRequestSerializer
    pagination_class = StudentLeaveRequestPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]


    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "StudentLeaveRequest lsit fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "StudentLeaveRequest create successfully"
            return response_handler(message=message , code= 200 , data = response.data)
        except ValidationError as e:
            return response_handler( message=format_serializer_errors(e.detail), code=400,data={})
        except Exception as e:
            if isinstance(e.args[0], dict):  
                formatted_errors = format_serializer_errors(e.args[0])
                return response_handler(message=formatted_errors[0], code=400, data={})
            else:
                return response_handler(message=str(e), code=400, data={})
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance , data = request.data , partial = True)
        if serializer.is_valid():
            serializer.save()
            message = "StudentLeaveRequest updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message=message , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            message = "StudentLeaveRequest data retrived successfully"
            return response_handler(message= message , code= 200 , data=serializer.data)
        except NotFound:
            return response_handler(message= "StudentLeaveRequest no found" , code = 400 , data={})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "StudentLeaveRequest delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "StudentLeaveRequest no found"
            return response_handler(message= message , code = 400 , data= {})
    
    @action(detail=True , methods=['post'])
    def status(self, request , pk = None):
        instance = self.get_object()
        serializer = self.serializer_class(instance , data = request.data , partial = True)
        if serializer.is_valid():
            serializer.save()
            if request.data.get('status') == "Approved":
                message = "Leave Approved successfully"
                return response_handler(message= message  , code = 200 , data = {})
            else:
                message = "Leave Rejected successfully"
                return response_handler(message = message , code = 200 , data={})
        messgae = "Leave status updation failed"
        return response_handler(message= message , code = 400 , data = {})
        