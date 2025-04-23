from rest_framework import viewsets
from modules.administration.models import *
from modules.users.models import *
from api.v1.module.serializers.exam_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from api.v1.module.response_handler import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from api.v1.module.serializers.student_serializer import *
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError , NotFound
import django_filters

class ExamFilter(django_filters.FilterSet):
    batch = django_filters.NumberFilter(field_name='component__subject_mapping__batch')
    subject_name = django_filters.CharFilter(field_name='component__subject_mapping__subject__name', lookup_expr='icontains')
    term = django_filters.NumberFilter(field_name='component__subject_mapping__term')

    class Meta:
        model = Exam
        fields = ['batch', 'subject_name', 'term']

class ExamPagination(PageNumberPagination):
    page_size = 10
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Exam no found' , 'code':400 , 'data':{} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Exam List fetch successfully"
        return Response({'message':message , 'code': 200 , 'data':data})

class ExamModelViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all().order_by('-id')
    serializer_class = ExamSerializer
    pagination_class = ExamPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends =[SearchFilter , DjangoFilterBackend]
    filterset_class = ExamFilter

    def get_serializer_class(self):
        if self.request.method =='GET':
            return ExamListtSerializer
        return ExamSerializer


    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Exam no found"
            return response_handler(message= message , code = 400 , data={})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Exam create successfully"
            return response_handler(message=message , code = 200  , data =  response.data)
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
        serializer =  self.serializer_class(instance , data = request.data , partial = True)
        if serializer.is_valid():
            serializer.save()
            message = "Exam Updated successfully"
            return response_handler(message = message , code = 200 , data = serializer.data)
        message = "Something went wrong"
        return response_handler(message=message , code = 400 , data = {})
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            response = self.get_serializer(instance )
            message = "Exam data retrived successfully"
            return response_handler(message = message , code = 200 , data = response.data)
        except NotFound:
            return response_handler(message="Exam No found" , code = 400 , data={})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Exam deleted successfully"
            return response_handler(message = message , code = 200 , data = {})
        except:
            message = "Exam no found"
            return response_handler(message=message , code = 400 , data = {})

    @action(detail= True , methods=['post'])
    def active(self, request , pk= None):
        instance = self.get_object()
        serializer = ExamActiveSerializer(instance , data = request.data)
        if serializer.is_valid():
            serializer.save()
            if request.data.get('is_active'):
                message = "Exam active successfully"
                return response_handler(message = message , code = 200 , data = {})
            else:
                message = "Exam Inactive Successfully"
                return response_handler(message = message , code = 200 , data = {})
        message = "Exam no found"
        return response_handler(message=message , code = 400  , data ={})
    
    @action(detail=True , methods=['post'])
    def cancel(self, request , pk = None):
        instance = self.get_object()
        serializer = ExamCancelSerializer(instance , data = request.data)
        if serializer.is_valid():
            serializer.save()
            if request.data.get('is_cancel'):
                message = "Exam Cancel successfully"
                return response_handler(message=message , code = 200 , data={})
            else:
                message = "Exam Permit successfully"
                return response_handler(message=message , code = 200 , data= {})
        message = "Exam No found"
        return response_handler(message=message , code = 400  , data={})
        



class ExamSubjectMappingListAPIView(APIView):
    def get(self, request):
        term_id = request.query_params.get("term_id")
        batch_id = request.query_params.get("batch_id")

        if not all([term_id, batch_id]):
            return response_handler(message="term_id and batch_id are required" , code= 400 , data= {})

        subject_mappings = SubjectMapping.objects.filter(
            term_id=term_id,
            batch_id=batch_id,
        ).distinct()
        serializer = ExamSubjectMappingSerializer(subject_mappings, many=True)
        return response_handler(message = "subject list fetched successfully" , code= 200 , data=serializer.data)
    
    def post(self, request):
        exam_data = request.data.get("exam_data", [])
        # import pdb ; pdb.set_trace()
        errors = []

        for exam in exam_data:
            component_id = exam.get("component_id")
            date = exam.get("date")
            start_time = exam.get("start_time")
            duration = exam.get("duration", 3)
            

            if not component_id:
                errors.append("Component ID is required.")
                continue

            try:
                component = Component.objects.get(id=component_id)
            except Component.DoesNotExist:
                errors.append(f"Component with id {component_id} not found.")
                continue

            # Subject Name for Error Message
            subject_name = getattr(component, "name", f"ID {component_id}")

            if not date:
                errors.append(f"Date is required for subject: {subject_name}")
                continue
            # import pdb ; pdb.set_trace()
            # Update if exam already exists for the component, else create new
            exam_obj, created = Exam.objects.update_or_create(
                component=component,
                defaults={
                    "date": date,
                    "start_time": start_time,
                    "duration": duration
                }
            )

        if errors:
            return response_handler(message=errors, code=400, data={})

        return response_handler(message="Exam Schedule processed successfully", code=200, data={})





class HallTicketAnnouncePagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'HallTicketAnnounce no found' , 'code':400 , 'data': {} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "HallTicketAnnounce list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class HallTicketAnnounceModelViewSet(viewsets.ModelViewSet):
    queryset = HallTicketAnnounce.objects.all().order_by('-id')
    serializer_class = HallTicketAnnounceSerializer
    pagination_class = HallTicketAnnouncePagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']

    def get_serializer_class(self):
        if self.request.method == "GET":
            return HallTicketAnnounceListSerializer
        return HallTicketAnnounceSerializer

    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "HallTicketAnnounce lsit fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "HallTicketAnnounce create successfully"
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
            message = "HallTicketAnnounce updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message=message , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        message = "HallTicketAnnounce data retrived successfully"
        return response_handler(message= message , code= 200 , data=serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "HallTicketAnnounce delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "HallTicketAnnounce no found"
            return response_handler(message= message , code = 400 , data= {})
        

class BatchWiseHallTicketAnnounce(APIView):
    def get(self, request , batch):
        announced =  HallTicketAnnounce.objects.filter(batch = batch , is_active = True)
        announced = HallTicketAnnounceListSerializer(announced , many = True)
        return response_handler(message="hall ticket announced successfully" , code =200 , data = announced.data)
    

class StudentWiseExamList(APIView):
    def get(self, request, student_id):
        term = request.query_params.get('term')
        student = get_object_or_404(Student, id=student_id)
        student_mapping = StudentMapping.objects.filter(student=student)
        if not term:
            subject_mappings = SubjectMapping.objects.filter(is_active = True)
        else:
            subject_mappings = SubjectMapping.objects.filter(term = term)
        subject_mappings = subject_mappings.filter(
            batch=student.batch,
            course=student.course,
            specialization__in=student_mapping.values_list('specialization', flat=True)
        )
        components = Component.objects.filter(subject_mapping__in=subject_mappings)
        exams = Exam.objects.filter(component__in=components).order_by('date')
        exam_data = ExamListtSerializer(exams, many=True).data
        return response_handler(message="Exam list fetched successfully",code=200, data=exam_data)
    





class ExamResultAnnouncePagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'ExamResultAnnounce no found' , 'code':400 , 'data': {} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "ExamResultAnnounce list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class ExamResultAnnounceModelViewSet(viewsets.ModelViewSet):
    queryset = ExamResultAnnounce.objects.all().order_by('-id')
    serializer_class = ExamResultAnnounceSerializer
    pagination_class = ExamResultAnnouncePagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]

    def get_serializer_class(self):
        if self.request.method =='GET':
            return ExamResultAnnounceListSerializer
        return ExamResultAnnounceSerializer
    
    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "ExamResultAnnounce lsit fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "ExamResultAnnounce create successfully"
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
            message = "ExamResultAnnounce updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message=message , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        message = "ExamResultAnnounce data retrived successfully"
        return response_handler(message= message , code= 200 , data=serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "ExamResultAnnounce delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "ExamResultAnnounce no found"
            return response_handler(message= message , code = 400 , data= {})
        

class BatchWiseExamResultAnnounce(APIView):
    def get(self, request , batch):
        announced =  ExamResultAnnounce.objects.filter(batch = batch , is_active = True)
        announced = ExamResultAnnounceListSerializer(announced , many = True)
        return response_handler(message="exam result announced successfully" , code =200 , data = announced.data)
    
