from rest_framework import viewsets
from modules.administration.models import  *
from api.v1.module.serializers.resit_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response  import Response
from api.v1.module.response_handler import *
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from modules.users.models import *
from api.v1.module.serializers.student_serializer import *
from api.v1.module.admin.subject_mapping_controller import *
import math

class ResetExamRequestPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Resit data no found' , 'code':400 , 'data':{} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Reset Data Retrived successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra':{'count':total_items , 'total': total_page , 'page_size': self.page_size}})

class ComponentPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message': 'Component no found' , 'code':400 , 'data':{} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Component list fetched successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra':{'count':total_items , 'total':total_page , 'page_size':self.page_size}})




class ResetExamRequestModelViewSet(viewsets.ModelViewSet):
    queryset = ResetExamRequest.objects.all().order_by('-id')
    serializer_class = ResetExamRequestSerializer
    pagination_class = ResetExamRequestPagination
    http_method_names = ['get' , 'post' , 'delete' , 'put']

    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            return response_handler(message= 'Resit data no found' , code=400  , data={})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args  , **kwargs)
            message = "Resit create successfully"
            return response_handler(message = message , code = 200 , data = response.data)
            
        except ValidationError as e:
            return response_handler( message=format_serializer_errors(e.detail), code=400,data={})
        except Exception as e:
            if isinstance(e.args[0], dict):  
                formatted_errors = format_serializer_errors(e.args[0])
                return response_handler(message=formatted_errors[0], code=400, data={})
            else:
                return response_handler(message=str(e), code=400, data={})
            

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        message = "Resit from retrived successfully"
        return response_handler(message= message  , code = 200  , data= serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance = instance , data = request.data , partial = True)
        if serializer.is_valid():
            serializer.save()
            message = "Resit data updated successfully"
            return response_handler(message=message , code = 200 , data = serializer.data)
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message = message , code = 400 , data = {})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Resit data delete successfully"
            return response_handler(message = message , code = 200 , data = {})
        except:
            return response_handler(message = "Resit data no found" , code = 400 , data={})



class ResetStudentComponentMarksUpdateAPI(APIView):
    def get(self , request , component_id):
        component = get_object_or_404(Component , id = component_id)
        subject_mapping = component.subject_mapping
        batch = component.subject_mapping.batch
        term  = component.subject_mapping.term
        course = component.subject_mapping.course.all()
        specialization = component.subject_mapping.specialization.all()
        reset_student = Student.objects.filter(resets__course__in = course , resets__batch = batch , resets__term = term , resets__specialization__in = specialization , resets__subjects_id=subject_mapping).distinct()
        student_serializer = StudentSerializer(reset_student , many = True)
        student_marks = { mark.student.id : mark.obtained_marks for mark in ComponentMarks.objects.filter(component = component_id)}
        for student in student_serializer.data:
            student['marks'] = student_marks.get(student['id'] , 00)
        message = "Resit component student list fetch successfully"
        return response_handler(message=message , code = 200 , data=student_serializer.data)
    
    def post(self , request , component_id):
        component = get_object_or_404(Component , id = component_id)
        subject_mapping = component.subject_mapping
        batch = component.subject_mapping.batch
        term  = component.subject_mapping.term
        course = component.subject_mapping.course.all()
        specialization = component.subject_mapping.specialization.all()
        reset_student = Student.objects.filter(resets__course__in = course , resets__batch = batch , resets__term = term , resets__specialization__in = specialization , resets__subjects_id=subject_mapping).distinct().values_list('id' , flat=True)
        student_serializer = StudentSerializer(reset_student , many = True)
        marks_objects = request.data.get('marks_student' , [])
        student_get_id = [marks_object['id'] for marks_object in marks_objects]
        if not set(student_get_id).issubset(set(reset_student)):
            return response_handler(message="Some students do not belong to this Reset" , code = 400 , data={})
        student_get_marks = [marks_object['marks'] for marks_object in marks_objects]
        if any(std_mark > component.max_marks for std_mark in student_get_marks):
            return response_handler(message="marks of student is equal and less then max marks of component" , code = 400 , data={})
        for marks_object in marks_objects:
            std = get_object_or_404(Student , id = marks_object['id'])
            ComponentMarks.objects.update_or_create(component = component , 
                        student =std,
                        defaults = {
                            'obtained_marks':marks_object['marks']
                        })
        message = "Resit Component marks uploaded successfully."
        return response_handler(message = message , code = 200 , data = {})
    

class StudentResetSubjectWiseGPAAPIView(APIView):
    def get(self, request , student_id, batch_id, term_id, course_id):
        reset_subject = SubjectMapping.objects.filter(resets__batch_id = batch_id , resets__course_id = course_id , resets__term_id = term_id , resets__student_id = student_id).distinct()
        subject_data = get_subject_data(student_id ,reset_subject)
        total_credit = sum(item['credit'] for item in subject_data.values())
        total_credit_xgp = sum(item['get_credit_xgp'] for item in subject_data.values())
        gpa = get_gpa(total_credit, total_credit_xgp)
            
        return JsonResponse({"message": "Reset result retrieved successfully",  "code" :200 ,"data": list(subject_data.values()) , "gpa":gpa  })



class StudentReset2SubjectWiseGPAAPIView(APIView):
    def get(self, request, student_id, batch_id, term_id, course_id):
        student_specializations = StudentMapping.objects.filter(
            student__id=student_id, batch_id=batch_id, term_id=term_id, course_id=course_id
        ).values_list("specialization", flat=True)

        subjects = SubjectMapping.objects.filter(
            batch_id=batch_id, term_id=term_id, course__id=course_id,
            specialization__id__in=student_specializations, type="main"
        ).select_related("subject").distinct()

        reset1_subjects = SubjectMapping.objects.filter(
            resets__batch_id=batch_id, resets__course_id=course_id,
            resets__term_id=term_id, resets__student_id=student_id , type = "resit-1"
        ).distinct()

        reset2_subjects = SubjectMapping.objects.filter(
            resets__batch_id=batch_id, resets__course_id=course_id,
            resets__term_id=term_id, resets__student_id=student_id , type = "resit-2"
        ).distinct()
        # import pdb; pdb.set_trace()

        subject_data = get_subject_data(student_id, subjects)
        reset1_subject_data = get_subject_data(student_id, reset1_subjects)
        reset2_subject_data = get_subject_data(student_id, reset2_subjects)

        for code, reset_data in reset1_subject_data.items():
            if code in subject_data and not subject_data[code]['is_pass']:
                subject_data[code] = reset_data
        for code, reset_data in reset2_subject_data.items():
            if code in reset1_subject_data and not reset1_subject_data[code]['is_pass']:
                subject_data[code] = reset_data

        total_credit = sum(item['credit'] for item in subject_data.values())
        total_credit_xgp = sum(item['get_credit_xgp'] for item in subject_data.values())
        gpa = get_gpa(total_credit, total_credit_xgp)

        return JsonResponse({"message": "Term result retrieved successfully", "code": 200, "data": list(subject_data.values()), "extra": gpa})





class StudentReset1SubjectWiseGPAAPIView(APIView):
    def get(self, request, student_id, batch_id, term_id, course_id):
        student_specializations = StudentMapping.objects.filter(
            student__id=student_id, batch_id=batch_id, term_id=term_id, course_id=course_id
        ).values_list("specialization", flat=True)

        subjects = SubjectMapping.objects.filter(
            batch_id=batch_id, term_id=term_id, course__id=course_id,
            specialization__id__in=student_specializations, type="main"
        ).select_related("subject").distinct()

        reset1_subjects = SubjectMapping.objects.filter(
            resets__batch_id=batch_id, resets__course_id=course_id,
            resets__term_id=term_id, resets__student_id=student_id , type = "resit-1"
        ).distinct()

        subject_data = get_subject_data(student_id, subjects)
        reset1_subject_data = get_subject_data(student_id, reset1_subjects)

        for code, reset_data in reset1_subject_data.items():
            if code in subject_data and not subject_data[code]['is_pass']:
                subject_data[code] = reset_data

        total_credit = sum(item['credit'] for item in subject_data.values())
        total_credit_xgp = sum(item['get_credit_xgp'] for item in subject_data.values())
        gpa = get_gpa(total_credit, total_credit_xgp)

        return JsonResponse({"message": "Term result retrieved successfully", "code": 200, "data": list(subject_data.values()), "extra": gpa})
