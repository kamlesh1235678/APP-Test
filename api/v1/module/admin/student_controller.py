import csv
import pandas as pd
from django.db import IntegrityError
from rest_framework import generics
from rest_framework.views import APIView
from api.v1.module.response_handler import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny,IsAdminUser
from rest_framework import viewsets
from modules.users.models import *
from api.v1.module.serializers.student_serializer import *
from api.v1.module.serializers.mix_serializer import *
import pdb,math , os
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import *
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError , NotFound
from django.conf import settings

class StudentPagination(PageNumberPagination):
  page_size = 10
  page_size_query_param = 'page_size'
  max_page_size = None
  def get_paginated_response(self, data):
    total_items = self.page.paginator.count
    if total_items == 0:
        return Response({'message': 'No Student data found','code': 400,'data': data,'extra': {
            'count': total_items,'total': 0,'page_size': self.page_size}})
    if self.request.query_params.get('page_size'):
      self.page_size = int(self.request.query_params.get('page_size'))
    total_page = math.ceil(self.page.paginator.count / self.page_size)
    message = 'Student list fetched successfully'
    return Response({'message':message,'code':200,'data':data,'extra':{'count':total_items,'total':total_page,'page_size':self.page_size} })





class StudentModelViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by('-id')
    serializer_class = StudentSerializer
    pagination_class = StudentPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]
   #  filterset_fields = ['name' , 'contact_number']

    def get_serializer_class(self):
        if self.request.method =='GET':
            return StudentListSerializer
        return StudentSerializer

    def get_queryset(self):
        try:
          return super().get_queryset()
        except:
           message = "Student No Found"
           return  response_handler(message= message , code= 400 , data={})
        
    def create(self, request, *args, **kwargs):
       try:
         response = super().create(request ,*args , **kwargs)
         message = "Student create successfully"
         return response_handler(message=message , code = 200 , data=response.data )
       except ValidationError as e:
         return response_handler( message=format_serializer_errors_nested(e.detail), code=400,data={})
       except Exception as e:
            if isinstance(e.args[0], dict):  
                formatted_errors = format_serializer_errors_nested(e.args[0])
                return response_handler(message=formatted_errors[0], code=400, data={})
            else:
                return response_handler(message=str(e), code=400, data={})
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        student_instance = self.get_object()
        # Extract user data from request data
        user_data = request.data.pop('user', None)
        if user_data:
            user_instance = student_instance.user  # Get the related User instance
            user_serializer = UserSerializer(user_instance, data=user_data, partial=True)
            if not user_serializer.is_valid():
               return response_handler(
                     message=format_serializer_errors(user_serializer.errors)[0],  # First error
                     code=400,
                     data={}
               )
            user_serializer.save()
        
        # Update the Student instance
        student_serializer = self.get_serializer(student_instance, data=request.data, partial=True)
        if student_serializer.is_valid():
            student_serializer.save()
            message = "Student data updated successfully"
            return response_handler(message=message , code = 200 , data= student_serializer.data)
        else:
            return response_handler(message=format_serializer_errors_nested(student_serializer.errors)[0] , code = 400 , data = {})
    
    def retrieve(self, request, *args, **kwargs):
       try:
         instance = self.get_object()
         response = self.get_serializer(instance)
         message = "Student data retrived successfully"
         return response_handler(message=message , code = 200 , data = response.data)
       except NotFound:
          return response_handler(message="Student no found" , code = 400 , data={})
    
    def destroy(self, request, *args, **kwargs):
        try:
          instance = self.get_object()
          user_instance = instance.user
          self.perform_destroy(user_instance)
          self.perform_destroy(instance)
          message = "Student deleted successfully"
          return response_handler(message= message , code= 200 , data ={})
        except:
           message = "Student no found"
           return response_handler(message=message , code = 400 , data ={})
        
    
    @action(detail=True, methods=['post'])
    def archived(self, request, pk=None):
        student = self.get_object()
        data = request.data.copy()
        data['is_lock'] = True
        user_lock = UserLockSerializer(student.user , data= data)
        user_lock.is_valid(raise_exception=True)
        user_lock.save()
        serializer = self.get_serializer(instance = student , data = request.data , partial = True)
        if serializer.is_valid():
            serializer.save()
            if request.data.get('is_archived'):
              message = "Student Archived successfully"
              return response_handler(message=message , code=200 , data={})
            else:
              message = "Student unarchived successfully"
              return response_handler(message=message , code = 200 , data ={})
        else:
           message = format_serializer_errors(serializer.errors)[0]
           return response_handler(message=message , code= 400 , data= {})
        
    @action(detail= True , methods=['post'])
    def lock(self, request , pk = None):
       instance = self.get_object()
       serializer = UserLockSerializer(instance.user , data = request.data)
       if serializer.is_valid():
          serializer.save()
          if request.data.get('is_lock'):
             message = "Student Locked successfully"
             return response_handler(message = message , code = 200 , data= {})
          else:
             message = "Student unlocked successfully"
             return response_handler(message= message , code = 200 ,data={})
       else:
          message = format_serializer_errors(serializer.errors)[0]
          return response_handler(message=message , code = 400 , data= {})
       
    @action(detail=True , methods=['Post'])
    def active(self,request , pk = None):
       instance = self.get_object()
       serializer = UserActiveSerializer(instance.user , data = request.data)
       if serializer.is_valid():
          serializer.save()
          if request.data.get('is_active'):
             message = "Student Active successfully"
             return response_handler(message = message , code = 200 , data={})
          else:
             message = "Student unactive successfully"
             return response_handler(message= message , code = 200 , data ={})
       else:
          message = format_serializer_errors(serializer.errors)[0]
          return response_handler(message=message , code = 400 , data= {})
       




        


class StudentDocumentPagination(PageNumberPagination):
   page_size = 10
   def get_paginated_response(self, data):
      total_items = self.page.paginator.count
      if not total_items:
         return Response({'message':'Document no found' , 'code':400 , 'data':{} , 'extra':{}})
      if self.page_size:
         total_page = math.ceil(total_items/self.page_size)
      message = "Document list getched successfully"
      return Response({'message':message , 'code':200 , 'data':data , 'extra':{'count':total_items , 'total':total_page , 'page_size':self.page_size}} )

class StudentDocumentModelSetView(viewsets.ModelViewSet):
   queryset = StudentDocument.objects.all().order_by('-id')
   serializer_class = StudentDocumentSerializer
   pagination_class  = StudentDocumentPagination
   http_method_names = ['get' , 'post' , 'put' , 'delete']

   def get_queryset(self):
      try:
        return super().get_queryset()
      except:
         return response_handler(message="document no found" , code = 200 , data= {})
      
   def create(self, request, *args, **kwargs):
      try:
        response = super().create(request , *args , **kwargs)
        message = "Document create successfully"
        return response_handler(message= message , code = 200 , data = response.data)
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
      old_file_path = instance.document_file.path if instance.document_file else None
      serializer = self.serializer_class(instance = instance , data = request.data , partial = True)
      if serializer.is_valid():
         serializer.save()
         if 'document_file' in request.data and old_file_path and os.path.exists(old_file_path):
            os.remove(old_file_path)
         message = "Document updated successfully"
         return response_handler(message=message , code = 200, data=serializer.data)
      else:
         message = format_serializer_errors(serializer.errors)[0]
         return response_handler(message=message , code= 400 , data={})
      
   def retrieve(self, request, *args, **kwargs):
      instance = self.get_object()
      serializer = self.get_serializer(instance)
      message = "document data retrived successfully"
      return response_handler(message=message , code = 200 , data = serializer.data)
   
   def destroy(self, request, *args, **kwargs):
      try:
         instance = self.get_object()
         old_file_path = instance.document_file.path if instance.document_file else None
         self.perform_destroy(instance)
         if old_file_path and os.path.exists(old_file_path):
            os.remove(old_file_path)
         message = "Document deleted sucessfully"
         return response_handler(message= message , code = 200 , data = {})
      except:
         message = "Document no found"
         return response_handler(message=message , code=400 , data={})
      

   @action(detail=False, methods=['get'], url_path='student-documents/(?P<student_id>\\d+)')
   def get_student_documents(self, request, student_id):
        documents = StudentDocument.objects.filter(student=student_id)
        serializer = self.get_serializer(documents, many=True)
        return response_handler(message='Student Document list fetched successfully' , code= 200 , data = serializer.data)
      
   
       




class UploadStudentExcel(APIView):
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
                    'user_type': "STUDENT"
                }

                student_data = {
                    'first_name': row['first_name'],
                    'middle_name': row.get('middle_name', ''),
                    'last_name': row['last_name'],
                    'contact_number': row['contact_number'],
                    'blood_group': row['blood_group'],
                    'date_of_birth': "2025-03-01",
                    # 'aadhar_number': row['aadhar_number'],
                    # 'tenth_score_type': row['tenth_score_type'],
                    'tenth_score': row['tenth_score'],
                    # 'twelfth_score_type': row['twelfth_score_type'],
                    'twelfth_score': row['twelfth_score'],
                    'graduation_background': row['graduation_background'],
                    # 'graduation_score_type': row['graduation_score_type'],
                    'graduation_score': row['graduation_score'],
                    'date_of_joining': "2025-03-01",
                    'gender': row['gender'],
                    'category': row['category'],
                    # 'experience_status': row['experience_status'],
                    'address': row['address'],
                    'city': row['city'],
                    'state': row['state'],
                    'pincode': row['pincode'],
                    'father_name': row['father_name'],
                    'father_contact_number': row['father_contact_number'],
                    # 'father_email': row.get('father_email', ''),
                    # 'father_aadhar_number': row['father_aadhar_number'],
                    'mother_name': row['mother_name'],
                    'mother_contact_number': row['mother_contact_number'],
                    # 'mother_email': row.get('mother_email', ''),
                    # 'mother_aadhar_number': row['mother_aadhar_number'],
                    # 'is_archived': row.get('is_archived', False),
                    'enrollment_number': row.get('enrollment_number', ''),
                    # 'aicte_permanent_id': row.get('aicte_permanent_id', ''),
                    'religion': row.get('religion', ''),
                    'district': row.get('district', ''),
                    'pwd': row.get('pwd', False),
                    'dropped': row.get('dropped', False),
                    'passout_status': row.get('passout_status', False),
                    'batch': row['batch'],
                    'course': row['course'],
                    'student_role': row['student_role'],
                }

                student_data['user'] = user_data
                serializer = StudentSerializer(data=student_data)

                if serializer.is_valid():
                    serializer.save()
                else:
                    errors.append({row['email']: serializer.errors})

            except IntegrityError as e:
                errors.append({row['email']: str(e)})

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Excel data successfully uploaded!', 'code': 200, 'data': {}}, status=status.HTTP_201_CREATED)




class StudentDetailAPIView(APIView):
    def get(self, request, pk):
        student = get_object_or_404(Student, id=pk)
        serializer = StudentMixSerializer(student)
        return response_handler(message='Student data retrived successfully' , code= 200 , data = serializer.data)
        






























# from io import TextIOWrapper
# from django.db import IntegrityError
# from datetime import datetime
# class UploadStudentCSV(APIView):
#     def post(self, request):
#         if 'csv_file' not in request.FILES:
#             return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

#         file = request.FILES['csv_file']

#         try:
#             data = file.read().decode('utf-8')
#         except UnicodeDecodeError:
#             data = file.read().decode('ISO-8859-1')

#         csv_file = io.StringIO(data)
#         reader = csv.DictReader(csv_file)

#         errors = []

#         for row in reader:
#             try:
#                 user_data = {
#                     'email': row['email'],
#                     'user_type': "STUDENT"
#                 }
#                 student_data = {
#                     'first_name': row['first_name'],
#                     'middle_name': row['middle_name'],
#                     'last_name': row['last_name'],
#                     'contact_number': row['contact_number'],
#                     'blood_group': row['blood_group'],
#                     'date_of_birth': "2025-03-01",
#                     'aadhar_number': row['aadhar_number'],
#                     'tenth_score_type': row['tenth_score_type'],
#                     'tenth_score': row['tenth_score'],
#                     'twelfth_score_type': row['twelfth_score_type'],
#                     'twelfth_score': row['twelfth_score'],
#                     'graduation_background': row['graduation_background'],
#                     'graduation_score_type': row['graduation_score_type'],
#                     'graduation_score': row['graduation_score'],
#                     'date_of_joining': "2025-03-01",
#                     'gender': row['gender'],
#                     'category': row['category'],
#                     'score_card': row['score_card'],
#                     'experience_status': row['experience_status'],
#                     'address': row['address'],
#                     'city': row['city'],
#                     'state': row['state'],
#                     'pincode': row['pincode'],
#                     'father_name': row['father_name'],
#                     'father_contact_number': row['father_contact_number'],
#                     'father_email': row.get('father_email', ''),
#                     'father_aadhar_number': row['father_aadhar_number'],
#                     'mother_name': row['mother_name'],
#                     'mother_contact_number': row['mother_contact_number'],
#                     'mother_email': row.get('mother_email', ''),
#                     'mother_aadhar_number': row['mother_aadhar_number'],
#                     'is_archived': row.get('is_archived', False),
#                     'enrollment_number': row.get('enrollment_number', ''),
#                     'aicte_permanent_id': row.get('aicte_permanent_id', ''),
#                     'religion': row.get('religion', ''),
#                     'district': row.get('district', ''),
#                     'pwd': row.get('pwd', False),
#                     'dropped': row.get('dropped', False),
#                     'passout_status': row.get('passout_status', False),
#                     'batch': row['batch'],
#                     'course': row['course'],
#                     'student_role': row['student_role'],
#                 }

#                 student_data['user'] = user_data
#                 serializer = StudentSerializer(data=student_data)
                
#                 if serializer.is_valid():
#                     serializer.save()
#                 else:
#                     errors.append({row['email']: serializer.errors})
#             except IntegrityError as e:
#                 errors.append({row['email']: str(e)})

#         if errors:
#             return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

#         return Response({'message': 'CSV data successfully uploaded!' , 'code':200 , 'data':{}}, status=status.HTTP_201_CREATED)






























































































































