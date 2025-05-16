from rest_framework import viewsets
from api.v1.module.response_handler import *
from django.contrib.auth.models import Group
from api.v1.module.serializers.permission_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
import math
from modules.privacy.models import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError , NotFound
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


        
class PermissionPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':"Permission no found" , 'code':400 , 'data':{} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Permission list fetche successfully"
        return Response({'message':message , 'code': 200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})


class PermissionModelViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all().order_by('-id')
    serializer_class = PermissionSerializer
    pagination_class = PermissionPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]
    filterset_fields = []

    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Permission no found"
            return response_handler(message = message , code = 400 , data={})
        
    def create(self, request, *args, **kwargs):
        response = super().create(request , *args , **kwargs)
        message = "Permission create successfully"
        return response_handler(message=message , code = 200 , data = {})
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance , data = request.data , partial  = True)
        if serializer.is_valid():
            serializer.save()
            message = "Permission updated successfully"
            return response_handler(message = message , code = 200 , data = serializer.data)
        else:
            message = format_serializer_errors(serializer.errors)[0]
            return response_handler(message= message , code = 400 , data={})
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            response = self.get_serializer(instance , many = True)
            message = "Permission data retrived successfully"
            return response_handler(message = message ,code = 200 , data = response.data)
        except NotFound:
            return response_handler(message = "Permission no found" , code = 400  , data={})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Permission deleted successfully"
            return response_handler(message=message , code = 200 , data={})
        except:
            message = "Permission no found"
            return response_handler(message = message , code = 400 , data = {})
        


class RolePermissionAPIView(APIView):
    def get(self, request , role_id):
        role = get_object_or_404(Role , id = role_id)
        excluded_content_type_ids = [1, 2, 3, 4, 5, 6, 10, 13, 41, 42, 43, 44, 45, 47]
        permissions = Permission.objects.exclude(content_type_id__in=excluded_content_type_ids).order_by('-id')
        permission_serializers = PermissionSerializer(permissions , many = True).data
        role_permission = role.role_permissions.all().first().permission.all().values_list('id', flat=True)
        grouped_permissions = {}

        for permission_serializer in permission_serializers:
            permission_serializer['has_permission'] = permission_serializer['id'] in role_permission
            content_type_name = permission_serializer['content_type']
            if content_type_name not in grouped_permissions:
                grouped_permissions[content_type_name] = []
            grouped_permissions[content_type_name].append(permission_serializer)
        data = {
            'permission': grouped_permissions,
        }
        message = "Permission fetched successfully"
        return response_handler(message =message , code = 200 , data = data)
    def post(self,request , role_id):
        role = get_object_or_404(Role , id = role_id)
        requestd_permission =   request.data.get('permission' , [])
        if not requestd_permission:
            return response_handler(message="Please Send At list one Permission" , code = 400 , data= {})
        permission = Permission.objects.filter(id__in = requestd_permission )
        # import pdb; pdb.set_trace()
        role_permission_obj ,create  = RolePermission.objects.update_or_create(role = role,
                                defaults = {})
        role_permission_obj.permission.set(permission)
        role_permission_obj.save()
        # 🔒 Blocklist tokens for all users who have this role (Student or Employee)
        try:
            if role_id == 3:
                # Special case: if this role is assigned to Students
                student_users = User.objects.filter(
                    student__student_role=role,
                    user_type="STUDENT"
                )

                for user in student_users:
                    tokens = OutstandingToken.objects.filter(user=user)
                    for token in tokens:
                        BlacklistedToken.objects.get_or_create(token=token)
            else:
                # General case: if this role is assigned to Employees
                employee_users = User.objects.filter(
                    employee__employee_role__in=[role],
                    user_type="EMPLOYEE"
                ).distinct()

                for user in employee_users:
                    tokens = OutstandingToken.objects.filter(user=user)
                    for token in tokens:
                        BlacklistedToken.objects.get_or_create(token=token)

        except Exception as e:
            print("Error blocklisting tokens:", e)

        message = "Permissions updated successfully"
        return response_handler(message=message , code = 200 , data={})