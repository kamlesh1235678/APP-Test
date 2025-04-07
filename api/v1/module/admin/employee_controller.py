from rest_framework import generics
from rest_framework.views import APIView
from api.v1.module.response_handler import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny,IsAdminUser
from rest_framework import viewsets
from modules.users.models import *
from api.v1.module.serializers.employee_serializer import *
import pdb,math
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import *
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError , NotFound
import pandas as pd
from django.db import IntegrityError


class EmployeePagination(PageNumberPagination):
  page_size = 10
  page_size_query_param = 'page_size'
  max_page_size = None
  def get_paginated_response(self, data):
    total_items = self.page.paginator.count
    if total_items == 0:
        return Response({'message': 'No Employee data found','code': 400,'data': data,'extra': {
            'count': total_items,'total': 0,'page_size': self.page_size}})
    if self.request.query_params.get('page_size'):
      self.page_size = int(self.request.query_params.get('page_size'))
    total_page = math.ceil(self.page.paginator.count / self.page_size)
    message = 'Employee list fetched successfully'
    return Response({'message':message,'code':200,'data':data,'extra':{'count':total_items,'total':total_page,'page_size':self.page_size} })







class EmployeeModelViewSet(viewsets.ModelViewSet):
   queryset = Employee.objects.all().order_by('-id')
   serializer_class = EmployeeSerializer
   pagination_class = EmployeePagination
   http_method_names = ['get' , 'post' , 'put' , 'delete']
   filter_backends = [SearchFilter , DjangoFilterBackend]
   # filterset_fields = ['name']

   def get_serializer_class(self):
      if self.request.method == 'GET':
         return EmployeeListSerializer
      return EmployeeSerializer

   def get_queryset(self):
      try:
         return super().get_queryset()
      except:
         message = "Employee no found"
         return response_handler(message=message , code= 400 , data= {})
      
   def create(self, request, *args, **kwargs):
      try:
         response = super().create(request, *args, **kwargs)
         message =  "Employee Create successfully"
         return response_handler(message= message , code=200 , data = response.data)
      except ValidationError as e:
         return response_handler( message=format_serializer_errors_nested(e.detail), code=400,data={})
      except Exception as e:
         if isinstance(e.args[0], dict):  
               formatted_errors = format_serializer_errors_nested(e.args[0])
               return response_handler(message=formatted_errors[0], code=400, data={})
         else:
               return response_handler(message=str(e), code=400, data={})
   
   def update(self, request, *args, **kwargs):
      partial =  kwargs.pop('partial' , False)
      
      employee_instance = self.get_object()
      user_data = request.data.pop('user' , None)
      if user_data:
          user_instance = employee_instance.user
          user_serializer = UserSerializer(user_instance , data = user_data ,context ={'require_password':False}, partial = True )
          if not user_serializer.is_valid():
            message = format_serializer_errors(user_serializer.errors)[0]
            return response_handler(message= message , code= 400 , data={})
          user_serializer.save()

      employee_serializer = self.get_serializer(employee_instance , data = request.data , partial = True)
      if employee_serializer.is_valid():
         employee_serializer.save()
         message = "Employee data Update successfully"
         return response_handler(message= message , code= 200 , data = employee_serializer.data)
      else:
         message = format_serializer_errors_nested(employee_serializer.errors)[0]
         return response_handler(message= message , code= 400 , data={})
      
   def retrieve(self, request, *args, **kwargs):
       try:
         instance = self.get_object()
         response = self.get_serializer(instance)
         message = "Employee data retrived successfully"
         return response_handler(message=message , code = 200 , data= response.data)
       except NotFound:
          return response_handler(message="Employee no found" , code = 400 , data={})
   def destroy(self, request, *args, **kwargs):
      try:
         instance = self.get_object()
         user_instance = instance.user
         self.perform_destroy(user_instance)
         self.perform_destroy(instance)
         message = "Employee data delete successfully"
         return response_handler(message= message , code = 200 , data={})
      except:
         message = "Employee no found"
         return response_handler(message= message , code= 400 , data={})
      
   @action(detail=True , methods=['post'])   
   def archived(self, request , pk = None):
      instance = self.get_object()
      data = request.data.copy()
      data['is_lock'] = True
      user_lock = UserLockSerializer(instance.user , data = data)
      user_lock.is_valid(raise_exception=True)
      user_lock.save()
      serializers = EmployeeArchivedSerializer(instance , data = request.data)
      if serializers.is_valid():
         serializers.save()
         if request.data.get('is_archived'):
            message = "Employee archived successfully"
            return response_handler(message=message , code = 200 , data={})
         else:
            message = "Employee unarchived successfully"
            return response_handler(message= message , code=400 , data={})
      else:
         message = format_serializer_errors(serializer.errors)[0]
         return response_handler(message=message , code= 400 , data ={})
      
   @action(detail=True , methods=['post'])
   def lock(self,request , pk= None):
      instance = self.get_object()
      serializer = UserLockSerializer(instance.user , data = request.data)
      if serializer.is_valid():
         serializer.save()
         if request.data.get('is_lock'):
            message = "Employee locked successfully"
            return response_handler(message=message , code = 200 , data={})
         else:
            message = "Employee unlocked sucessfully"
            return response_handler(message=message , code = 200 , data={})
      else:
         message = format_serializer_errors(serializer.errors)[0]
         return response_handler(message=message , code = 400 , data={})
      
   @action(detail=True , methods=['Post'])
   def active(self,request , pk = None):
      instance = self.get_object()
      serializer = UserActiveSerializer(instance.user , data = request.data)
      if serializer.is_valid():
         serializer.save()
         if request.data.get('is_active'):
            message = "Employee Active successfully"
            return response_handler(message = message , code = 200 , data={})
         else:
            message = "Employee Inactive successfully"
            return response_handler(message= message , code = 200 , data ={})
      else:
         message = format_serializer_errors(serializer.errors)[0]
         return response_handler(message=message , code = 400 , data= {})

        


class FacultyMentorshipPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Faculty Mentorship no found' , 'code':400 , 'data': {} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Faculty Mentorship list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class FacultyMentorshipModelViewSet(viewsets.ModelViewSet):
    queryset = FacultyMentorship.objects.all().order_by('-id')
    serializer_class = FacultyMentorshipSerializer
    pagination_class = FacultyMentorshipPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FacultyMentorshipListSerializer
        return FacultyMentorshipSerializer


    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Faculty Mentorship lsit fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        batch = request.data.get('batch')
        course = request.data.get('course')
        faculty = request.data.get('user')
        if FacultyMentorship.objects.filter(user = faculty ,  students__batch=batch, students__course=course).exists():
           return response_handler(message='Students already assign this Faculty' , code = 400 , data={})
        
        try:
            response = super().create(request , *args , **kwargs)
            message = "Faculty Mentorship create successfully"
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
            message = "Faculty Mentorship updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message=message , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            message = "Faculty Mentorship data retrived successfully"
            return response_handler(message= message , code= 200 , data=serializer.data)
        except NotFound:
            return response_handler(message="FacultyMentorship no found" , code = 400 , data={})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Faculty Mentorship delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "Faculty Mentorship no found"
            return response_handler(message= message , code = 400 , data= {})
        
    @action(detail=False, methods=['get'], url_path='students-by-faculty/(?P<faculty_id>\d+)')
    def students_by_faculty(self, request, faculty_id):
        faculty = get_object_or_404(Employee, id=faculty_id)
        mentorship = FacultyMentorship.objects.filter(user=faculty).first()

        if mentorship:
            students = mentorship.students.all()
            student_data = StudentMixSerializer(students , many = True)
            return Response({"message": "Assigned student list fetched successfully", "code": 200, "data": student_data.data})
        else:
            return Response({"message": "No students found for this faculty.", "code": 400, "data": {}})








class UploadEmployeeExcel(APIView):
    def post(self, request):
        if 'excel_file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['excel_file']

        try:
            df = pd.read_excel(file, dtype=str)  # Read Excel file into a DataFrame
        except Exception as e:
            return Response({'error': f'Error reading file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        errors = []

        for _, row in df.iterrows():
            try:
                user_data = {
                    'email': row['email'],
                    'user_type': "EMPLOYEE"
                }

                employee_data = {
                    "salutation": row['salutation'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'contact_no': row['contact_no'],
                    'date_of_birth': "2025-03-01",
                    "employee_role": row['employee_role'],
                    "employee_type": row['employee_type'],
                }

                employee_data['user'] = user_data
                serializer = EmployeeSerializer(data=employee_data)

                if serializer.is_valid():
                    serializer.save()
                else:
                    errors.append({row['email']: serializer.errors})

            except IntegrityError as e:
                errors.append({row['email']: str(e)})

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Excel data successfully uploaded!', 'code': 200, 'data': {}}, status=status.HTTP_201_CREATED)





