from rest_framework import viewsets
from modules.administration.models import *
from api.v1.module.serializers.student_serializer import *
from api.v1.module.serializers.mix_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from api.v1.module.response_handler import *
from rest_framework.views import  APIView
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError , NotFound
from django.db.models import Q

class StudentMappingPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Student Mapping no found' , 'code':400 , 'data': {} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Student Mapping list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class StudentMappingModelViewSet(viewsets.ModelViewSet):
    queryset = StudentMapping.objects.all().order_by('-id')
    serializer_class = StudentMappingSerializer
    pagination_class = StudentMappingPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]
    filterset_fields = ['student__first_name' ]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return StudentMappingLListSerializer
        return StudentMappingSerializer
    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Student Mapping lsit fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Student Mapping create successfully"
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
            message = "Student Mapping updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message=message , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            message = "Student Mapping data retrived successfully"
            return response_handler(message= message , code= 200 , data=serializer.data)
        except NotFound:
            return response_handler(message="Student Mapping not found" , code = 400 , data = {})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Student Mapping delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "Student Mapping no found"
            return response_handler(message= message , code = 400 , data= {})
        


class StudentSpecializationAPIView(APIView):
    def get(self, request , term_id):
        if request.user.is_authenticated:
            if request.user.student:
                student_id = request.user.student.id
                student = get_object_or_404(Student , id = student_id)
                specialization = StudentMapping.objects.filter(batch = student.batch , course = student.course , term = term_id)
                specialization = StudentSpecilaizationSerializer(specialization , many = True , context={'student': student})
                return response_handler(message = 'specialization list fetched successfully' , code = 200,  data=specialization.data)
            return response_handler(message='Student access only' , code=400 , data={})
        return response_handler(message="You Not authenticated dear" , code = 400 , data={})
    
    def post(self, request , term_id):
        if request.user.is_authenticated:
            student_id = request.user.student.id
            student = get_object_or_404(Student , id = student_id)
            current_ids = StudentMapping.objects.filter(batch = student.batch , course = student.course , term = term_id).values_list('id' , flat=True)
            for current_id in current_ids:
                current_student_mapping = get_object_or_404(StudentMapping, id=current_id)
                current_student_mapping.student.remove(student)
            mapping_ids = request.data.get('mapping_ids' , [])
            for mapping_id in mapping_ids:
                student_mapping = get_object_or_404(StudentMapping, id=mapping_id)
                if student_mapping.student.filter(id=student.id).exists():
                    return response_handler(message = "You are already in selection , choose another selection" ,code = 400, data={} )
                student_mapping.student.add(student)
            return response_handler(message="Your Selection added successfully" , code = 200 , data={})
        else:
            return response_handler(message = "You Not authenticated dear" ,code = 400, data={} )
        
class PromoteStudentInTermAPIView(APIView):
    def post(self, request):
        last_terms_data = request.data.get("last_terms_data", [])
        up_coming_term = request.data.get("term")

        if not last_terms_data or not up_coming_term :
            return response_handler(message = "Invalid data provided" ,code = 400, data={} )

        for last_term in last_terms_data:
            last_term = get_object_or_404(StudentMapping , id = last_term)
            term = get_object_or_404(Terms , id = up_coming_term)
            new_mapping , created= StudentMapping.objects.get_or_create(
                term=term,
                batch = last_term.batch,
                course = last_term.course,
                specialization=last_term.specialization
            )
            new_mapping.student.set(last_term.student.all())
            new_mapping.save()
        return response_handler(message = "Student promoted successfully" ,code = 200, data={} )
    

class StudentMappingFilter(APIView):
    def get(self, request):
        course = request.query_params.get('course')
        batch = request.query_params.get('batch')
        term = request.query_params.get('term')
        filters = Q()
        if course:
            filters &= Q(course = course)
        if batch:
            filters &= Q(batch= batch)
        if term:
            filters &= Q(term= term)
        student_mapping =  StudentMapping.objects.filter(filters).order_by('-id')
        student_mapping =  StudentMappingFiterSerializer(student_mapping , many = True)
        return response_handler(message='filtered student mapping list fetched successfully' , code= 200 , data=student_mapping.data)




class StudentMappingEditAPIView(APIView):
    def get(self, request , student_mapping_id):
        student_mapping = get_object_or_404(StudentMapping , id = student_mapping_id)
        course_id = student_mapping.course
        batch_id = student_mapping.batch
        # Fetch students of this course & batch
        students = Student.objects.filter(course_id=course_id, batch_id=batch_id ,dropped = False , is_archived = False).order_by('-id')

        mapped_students = set(student_mapping.student.values_list('id', flat=True))

        # Serialize with 'checked' field
        serialized_students = []
        for student in students:
            data = StudentMixSerializer(student).data
            data['checked'] = student.id in mapped_students
            serialized_students.append(data)
        return response_handler(message = "Student list with mapping status fetched successfully" ,code = 200 , data=serialized_students )
        
    
    def post(self, request, student_mapping_id):
        student_mapping = get_object_or_404(StudentMapping, id=student_mapping_id)
        student_ids = request.data.get("student_ids", [])

        if not isinstance(student_ids, list):
            return response_handler(message="student_ids must be a list of student IDs" , code = 400 , data={})
        # Validate all student IDs belong to the correct batch & course
        valid_students = Student.objects.filter(
            id__in=student_ids,
            course_id=student_mapping.course_id,
            batch_id=student_mapping.batch_id,
            dropped=False,
            is_archived=False
        )
        # Update mapping
        student_mapping.student.set(valid_students)
        student_mapping.save()
        return response_handler(message="Student mapping updated successfully" , code = 200 , data = {})