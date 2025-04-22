from django.http import JsonResponse
from rest_framework import viewsets
from modules.administration.models import *
from api.v1.module.serializers.subject_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from api.v1.module.response_handler import *
from rest_framework.exceptions import ValidationError , NotFound
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from modules.users.models import Student
from django_filters import rest_framework as filters

class MyFilterSet(filters.FilterSet):
    course = filters.BaseInFilter(field_name='course', lookup_expr='in')

    class Meta:
        model = SubjectMapping
        fields = ['subject__name', 'term', 'batch', 'faculty__first_name', 'course']


class SubjectMappingPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Subject Mapping no found' , 'code':400 , 'data': {} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Subject Mapping  list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class SubjectMappingModelViewSet(viewsets.ModelViewSet):
    queryset = SubjectMapping.objects.all().order_by('-id')
    serializer_class = SubjectMappingSerializer
    pagination_class = SubjectMappingPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]
    filterset_class = MyFilterSet

    def get_serializer_class(self):
        if self.request.method =='GET':
            return SubjectMappingListSerializer
        return SubjectMappingSerializer

    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Subject Mapping  list fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Subject Mapping  create successfully"
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
        # import pdb; pdb.set_trace()
        if serializer.is_valid():
            serializer.save()
            message = "Subject Mapping  updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = serializer.errors.get("non_field_errors", "Validation failed")
        return response_handler(message=str(message[0]) , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            message = "Subject Mapping  data retrived successfully"
            return response_handler(message= message , code= 200 , data=serializer.data)
        except NotFound:
            return response_handler(message= "Subject mapping not found" , code = 400 , data={})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Subject Mapping  delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "Subject Mapping  no found"
            return response_handler(message= message , code = 400 , data= {})
        

class BulkSubjectMappingCreateView(APIView):
    pass
    # def post(self, request):
    #     subjects = request.data.get("subjects", [])
    #     batch = request.data.get("batch")
    #     term = request.data.get("term")
    #     total_classes = request.data.get("total_classes")
    #     classes_completed = request.data.get("classes_completed", 0)
    #     weightage_external = request.data.get("weightage_external")
    #     weightage_internal = request.data.get("weightage_internal")
    #     mapping_type = request.data.get("type")
    #     faculty = request.data.get("faculty")
        
        
    #     for subject in subjects:
    #         batch = get_object_or_404(Batch , id = batch)
    #         term = get_object_or_404(Terms , id = term)
    #         faculty = get_object_or_404("Employee" , id = faculty)
    #         term = get_object_or_404(Terms , id = term)
    #         mapping = SubjectMapping.objects.create(
    #             batch=batch,
    #             term=term,
    #             total_classes=total_classes,
    #             classes_completed=classes_completed,
    #             weightage_external=weightage_external,
    #             weightage_internal=weightage_internal,
    #             type=mapping_type,
    #             faculty=faculty,
    #             subject=subject
    #         )
        
    #     return Response({"message": "Subjects mapped successfully"}, status=200)



def get_external_marks(student_id  , subject_mapping ):
    external_marks = ComponentMarks.objects.filter(
        student_id=student_id,
        component__subject_mapping=subject_mapping,
        component__type="EXTERNAL"
    ).aggregate(total_marks=Sum("obtained_marks"))["total_marks"] or 0  # Default to 0 if None
    max_external = Component.objects.filter(subject_mapping =subject_mapping , type = "EXTERNAL").aggregate(max_marks = Sum("max_marks"))['max_marks'] or 0
    # import pdb; pdb.set_trace()
    external_marks  = (external_marks/max_external)* subject_mapping.weightage_external
    return external_marks

def get_internal_marks(student_id  , subject_mapping ):
    internal_marks = ComponentMarks.objects.filter(
        student_id=student_id,
        component__subject_mapping=subject_mapping,
        component__type="INTERNAL"
    ).aggregate(total_marks=Sum("obtained_marks"))["total_marks"] or 0  # Default to 0 if None
    max_internal = Component.objects.filter(subject_mapping =subject_mapping , type = "INTERNAL").aggregate(max_marks = Sum("max_marks"))['max_marks'] or 0
    internal_marks  = (internal_marks/max_internal) * subject_mapping.weightage_internal
    return internal_marks

def get_passed(external_marks , internal_marks ,subject_mapping ):
    is_pass =  external_marks >= (0.5 * subject_mapping.weightage_external) and internal_marks >= (0.5 * subject_mapping.weightage_internal)
    return is_pass

def get_grade(total_marks):
    if total_marks > 91:
        return "A+"
    elif total_marks >= 81:
        return "A"
    elif total_marks >= 71:
        return "B+"
    elif total_marks >= 61:
        return "B"
    elif total_marks >= 50:
        return "C+"
    else:
        return "F"

def get_grade_point(total_marks):
    if total_marks >= 91:
        return 10
    elif total_marks >= 81:
        return 9
    elif total_marks >= 71:
        return 8
    elif total_marks >= 61:
        return 7
    elif total_marks >= 50:
        return 6
    else:
        return 0

def get_credit_xgp(credit , grade_point):
    credit_xgp = credit * grade_point
    return credit_xgp

def get_gpa(total_credit,total_credit_xgp ):
    try:
        gpa = total_credit_xgp/total_credit
        return gpa
    except:
        return 0
    
def att_percentage(student_id , subject_mapping_id):
    mapping_subject =  get_object_or_404(SubjectMapping , id = subject_mapping_id)
    student =  get_object_or_404(Student , id = student_id)
    attended_classes = Attendance.objects.filter(student = student ,  class_schedule__mapping =   mapping_subject , is_persent = True).count()
    complete_classes = mapping_subject.classes_completed
    attended_percentage = (attended_classes /complete_classes)*100 if complete_classes > 0 else 0
    return attended_percentage

def get_subject_data(student_id ,subject_mappings):
    data = {}
    for sub_map in subject_mappings:
        attendance_percentage = att_percentage(student_id, sub_map.id)
        
        if attendance_percentage>= 85:
            external_marks = get_external_marks(student_id, sub_map)
            internal_marks = get_internal_marks(student_id, sub_map)
            is_pass = get_passed(get_external_marks(student_id, sub_map), get_internal_marks(student_id, sub_map), sub_map)
            total_marks = get_internal_marks(student_id, sub_map) + get_external_marks(student_id, sub_map)
            grade = get_grade(total_marks)
            grade_point= get_grade_point(total_marks)
            credit_xgp= get_credit_xgp(sub_map.subject.credit, get_grade_point(total_marks))
        elif 85 > attendance_percentage >= 75:
            external_marks = get_external_marks(student_id, sub_map)
            internal_marks = get_internal_marks(student_id, sub_map)
            is_pass = get_passed(get_external_marks(student_id, sub_map), get_internal_marks(student_id, sub_map), sub_map)
            total_marks = get_internal_marks(student_id, sub_map) + get_external_marks(student_id, sub_map)
            grade = get_grade(total_marks-10)
            grade_point= get_grade_point(total_marks)
            credit_xgp= get_credit_xgp(sub_map.subject.credit, get_grade_point(total_marks))
        elif 75 > attendance_percentage >= 60:
            external_marks = get_external_marks(student_id, sub_map)
            internal_marks = get_internal_marks(student_id, sub_map)
            is_pass = get_passed(get_external_marks(student_id, sub_map), get_internal_marks(student_id, sub_map), sub_map)
            total_marks = get_internal_marks(student_id, sub_map) + get_external_marks(student_id, sub_map)
            grade = get_grade(total_marks)
            grade_point= get_grade_point(total_marks)
            credit_xgp= get_credit_xgp(sub_map.subject.credit, get_grade_point(total_marks))
        else:
            external_marks = 0
            internal_marks = 0
            is_pass = False
            total_marks = 0
            grade = "F"
            grade_point= 0
            credit_xgp= 0

        data[sub_map.subject.code] = {
            "Subject Name": sub_map.subject.name,
            "Subject Code": sub_map.subject.code,
            "External Marks": external_marks,
            "Internal Marks": internal_marks,
            "is_pass": is_pass ,
            "total_marks": total_marks,
            "grade": grade,
            "credit": sub_map.subject.credit,
            "grade_point": grade_point,
            "get_credit_xgp": credit_xgp
        }
    return data



class ExamResultGPAAPIView(APIView):
    def post(self, request):
        enrollment_number = request.data.get('enrollment_number')
        type = request.data.get('type')
        term_id = request.data.get('term')
        try:
            student =  Student.objects.filter(enrollment_number = enrollment_number).first()
        except Student.DoesNotExist:
            return response_handler(message="Student not found" , code = 400 , data= {})

        student_id = student.id
        batch_id = student.batch.id
        course_id = student.course.id
        student_specializations = StudentMapping.objects.filter(
            student__id=student_id, 
            batch_id=batch_id,
            term_id=term_id,
            course_id=course_id
        ).values_list("specialization", flat=True)
        subjects = SubjectMapping.objects.filter(
            batch_id=batch_id,
            term_id=term_id,
            course__id=course_id,
            specialization__id__in=student_specializations ,
            type = type , 
            is_active = True
        ).select_related("subject").distinct()
        

        subject_data = get_subject_data(student_id ,subjects)
        total_credit = sum(item['credit'] for item in subject_data.values())
        total_credit_xgp = sum(item['get_credit_xgp'] for item in subject_data.values())
        gpa = get_gpa(total_credit, total_credit_xgp)
            
        return JsonResponse({"message": "Term result retrieved successfully",  "code" :200 ,"data": list(subject_data.values())  , "extra":gpa })
    


class SubjectMappingSyllabusPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Syllabus no found' , 'code':400 , 'data': {} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Syllabus list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class SubjectMappingSyllabusModelViewSet(viewsets.ModelViewSet):
    queryset = SubjectMappingSyllabus.objects.all().order_by('-id')
    serializer_class = SubjectMappingSyllabusSerializer
    pagination_class = SubjectMappingSyllabusPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]


    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Syllabus list fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Syllabus create successfully"
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
            message = "Syllabus updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message=message , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        message = "Syllabus data retrived successfully"
        return response_handler(message= message , code= 200 , data=serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Syllabus delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "Syllabus no found"
            return response_handler(message= message , code = 400 , data= {})
        

class SubjectMappingSyllabusAPI(APIView):
    def get(self, request, subject_mapping_id):
        try:
            syllabus = SubjectMappingSyllabus.objects.get(mapping_id=subject_mapping_id)
            serializer = SubjectMappingSyllabusListSerializer(syllabus)
            return response_handler(message= "syllabus data retrived successfully" , code = 200 , data= serializer.data)
            
        except SubjectMappingSyllabus.DoesNotExist:
            return response_handler(message= "Syllabus not found" , code = 400 , data= {})

    def post(self, request, subject_mapping_id):
        try:
            syllabus, created = SubjectMappingSyllabus.objects.get_or_create(
                mapping_id=subject_mapping_id,
                defaults={'description': request.data.get('description', '')}
            )
            if not created:
                syllabus.description = request.data.get('description', syllabus.description)
                syllabus.save()

            serializer = SubjectMappingSyllabusSerializer(syllabus)
            return response_handler(message= "syllabus data updated successfully" , code = 200 , data= serializer.data)
        except SubjectMapping.DoesNotExist:
            return response_handler(message= "Invalid subject mapping id" , code = 400 , data= {})
        


class SubjectMappingStatusAPIview(APIView):
    def post(self, request):
        subject_mapping_ids = request.data.get("subject_mapping_ids" , []) # [{id , status} , {id , status}]
        for subject_mapping in subject_mapping_ids:
            SubjectMapping.objects.filter(pk = subject_mapping[0]).update(is_active = subject_mapping[1])
        return response_handler(message="Status Update successfully" , code = 200 , data={})