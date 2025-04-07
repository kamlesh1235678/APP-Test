from rest_framework import viewsets
from rest_framework.views import APIView
from api.v1.module.response_handler import response_handler
from api.v1.module.serializers.profile_serializer import *
from api.v1.module.response_handler import format_serializer_errors
from rest_framework.permissions import AllowAny



class StudentProfileAPIView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return None
            if request.user.user_type == 'STUDENT':
                user = request.user
                user_serializer = StudentProfileSerializer(user)
            return response_handler(message="Profile Retrived successfully" , code = 200 , data=user_serializer.data)
        return response_handler(message = "User not authenticated" , code = 400 , data={})
    def post(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return None
            if request.user.user_type == 'STUDENT':
                user = request.user.student
                user_data = request.data.pop('user', None)
                if user_data:
                    user_instance = request.user  # Get the related User instance
                    user_serializer = UserSerializer(user_instance, data=user_data, partial=True)
                    if not user_serializer.is_valid():
                        return response_handler(
                            message=format_serializer_errors(user_serializer.errors)[0],  # First error
                            code=400,
                            data={}
                        )
                    user_serializer.save()
                student_serializer = StudentSerializer(instance = user , data = request.data , partial = True)
                if student_serializer.is_valid():
                    student_serializer.save()
                    message = "Profile Updated successfully"
                    return response_handler(message=message , code= 200 , data = {})
                return response_handler(message=format_serializer_errors(student_serializer.errors)[0] , code = 400 , data = {})
            return response_handler(message='Only Student Profile allowed' , code = 400 , data= {})
        return response_handler(message='User Not authenticated'  , code = 400 , data= {})
    



class EmployeeProfileAPIView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.user_type == 'EMPLOYEE':
                user = request.user
                user_serializer = EmployeeProfileSerializer(user)
            return response_handler(message="Profile Retrived successfully" , code = 200 , data=user_serializer.data)
        return response_handler(message = "User not authenticated" , code = 400 , data={})
    def post(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return None
            if request.user.user_type == 'EMPLOYEE':
                user = request.user.employee
                user_data = request.data.pop('user', None)
                if user_data:
                    user_instance = request.user  # Get the related User instance
                    user_serializer = UserSerializer(user_instance, data=user_data, partial=True)
                    if not user_serializer.is_valid():
                        return response_handler(
                            message=format_serializer_errors(user_serializer.errors)[0],  # First error
                            code=400,
                            data={}
                        )
                    user_serializer.save()
                employee_serializer = EmployeeSerializer(instance = user , data = request.data , partial = True)
                if employee_serializer.is_valid():
                    employee_serializer.save()
                    message = "Profile Updated successfully"
                    return response_handler(message=message , code= 200 , data = {})
                return response_handler(message=format_serializer_errors(employee_serializer.errors)[0] , code = 400 , data = {})
            return response_handler(message='Only Employee profile allowed' , code = 400  , data = {})
        return response_handler(message='User Not authenticated'  , code = 400 , data= {})




        