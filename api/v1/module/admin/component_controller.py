from rest_framework import viewsets
from modules.administration.models  import *
from api.v1.module.serializers.component_serializer import *
from api.v1.module.serializers.mix_serializer import *
from rest_framework.pagination import PageNumberPagination
from api.v1.module.response_handler import *
from rest_framework.response import Response
import math
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from api.v1.module.serializers.student_serializer import *
from rest_framework.exceptions import ValidationError
from datetime import datetime , timedelta


class ComponentPagination(PageNumberPagination):
    page_size = 100
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message': 'Component no found' , 'code':400 , 'data':[] , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Component list fetched successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra':{'count':total_items , 'total':total_page , 'page_size':self.page_size}})


class ComponentModelViewSet(viewsets.ModelViewSet):
    queryset = Component.objects.all().order_by('-id')
    serializer_class = ComponentSerializer
    pagination_class = ComponentPagination
    http_method_names = ['get' , 'post' , 'delete' , 'put']
    filter_backends = [DjangoFilterBackend , SearchFilter]
    filterset_fields = []

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ComponentMixListSerializer
        return ComponentSerializer

    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Component no found"
            return response_handler(message= message , code = 400 , data = {})
    
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Component create successfully"
            return response_handler(message  = message , code = 200 , data = response.data)
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
        message = "Component data retrived successfully"
        return response_handler(message= message , code = 200 , data=serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance , data = request.data ,partial = True )
        if serializer.is_valid():
            serializer.save()
            message = "Component updated successfully"
            return response_handler(message = message , code = 200  , data = serializer.data)
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message = message , code = 400 , data = {})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Component deleted successfully"
            return response_handler(message = message , code = 200 , data = {})
        except:
            message = "Component no found"
            return response_handler(message=message , code = 400 , data= {})
        

class SubComponentAPIView(APIView):
    def get(self,request , component_id):
        sub_component  = SubComponent.objects.filter(component = component_id)
        sub_component_serializers = SubComponentSerializer(sub_component , many = True)
        return response_handler(message = 'SubComponent list fetched successfully' , code = 200 , data = sub_component_serializers.data)
    def post(self, request , component_id):
        component = get_object_or_404(Component , id = component_id)
        if not component.has_subcomponents:
            return response_handler(message='Component have no SubComponent , Please check' ,  code=400 , data = {})
        component_max_marks = component.max_marks
        requested_subcomponent_data = request.data.get('subcomponent_data' , [])
        total_marks = 0
        for x in requested_subcomponent_data:
            total_marks += x['max_marks']
        if total_marks != component_max_marks:
            return response_handler(message= 'Mismatch: Total marks and component marks sum are not equal !.' , code = 400  , data = {})
        SubComponent.objects.filter(component = component_id).delete()
        for x in requested_subcomponent_data:
            subcomponent = SubComponent.objects.create(component = component,
                                    name = x['name'] ,
                                    max_marks =  x['max_marks'] ,
                                    description=x.get('description'),
                                    start_date=x.get('start_date'),  
                                    end_date=x.get('end_date'),
                                    is_submission=x.get('is_submission', False), 
                                    is_active=x.get('is_active', True)  )
        message = "SubComponent created successfully"
        return response_handler(message= message , code = 200 , data = {})
    

class ComponentMarksAPIView(APIView):
    def get(self,request , component_id):
        component = get_object_or_404(Component , id = component_id)
        course = component.subject_mapping.course.all()
        batch = component.subject_mapping.batch
        term =  component.subject_mapping.term
        specialization= component.subject_mapping.specialization.all()
        type = component.subject_mapping.type
        if type == "main":
            component_student = Student.objects.filter(student_mappings__course__in = course , student_mappings__batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ,  dropped = False , is_archived =  False , user__is_active = True).distinct()
        else:
            component_student = Student.objects.filter(resets__batch=batch,resets__term=term,resets__course__in=course , resets__type= type , resets__subjects = component.subject_mapping.id ,  dropped = False , is_archived =  False , user__is_active = True ).distinct()
        student_serializer = StudentMixSerializer(component_student , many = True)
        student_marks = { mark.student.id : mark.obtained_marks for mark in ComponentMarks.objects.filter(component = component_id)}
        for student in student_serializer.data:
            student['marks'] = student_marks.get(student['id'] , 00)
            if component.is_submission:
                if ComponentAnswers.objects.filter(student=student["id"],component=component_id).exists():
                    
                    student["submitted"] = True
                else:
                    student["submitted"]  = False
            else:
                student["submitted"] = True
        message = "component student list fetch successfully"
        return response_handler(message=message , code = 200 , data=student_serializer.data , extra={'max_marks':component.max_marks})
    
    def post(self, request , component_id):
        component = get_object_or_404(Component , id = component_id)
        course = component.subject_mapping.course.all()
        batch = component.subject_mapping.batch
        term =  component.subject_mapping.term
        specialization= component.subject_mapping.specialization.all()
        type = component.subject_mapping.type
        if type == "main":
            component_student = Student.objects.filter(student_mappings__course__in = course , student_mappings__batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ,  dropped = False , is_archived =  False , user__is_active = True).distinct().values_list('id' , flat=True)
        else:
            component_student = Student.objects.filter(resets__batch=batch,resets__term=term,resets__course__in=course , resets__type= type ,  resets__subjects = component.subject_mapping.id ,  dropped = False , is_archived =  False , user__is_active = True).distinct().values_list('id' , flat=True)
        marks_objects = request.data.get('marks_student' , [])
        student_get_id = [marks_object['id'] for marks_object in marks_objects]
        if not set(student_get_id).issubset(set(component_student)):
            return response_handler(message="Some students do not belong to this class" , code = 400 , data={})
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
        message = "Component marks uploaded successfully."
        return response_handler(message = message , code = 200 , data = {})
    

class SubComponentMarksAPIView(APIView):
    def get(self, request , subcomponent_id):
        subcomponent = get_object_or_404(SubComponent , id = subcomponent_id)
        course = subcomponent.component.subject_mapping.course.all()
        batch = subcomponent.component.subject_mapping.batch
        term =  subcomponent.component.subject_mapping.term
        specialization= subcomponent.component.subject_mapping.specialization.all()
        type = subcomponent.component.subject_mapping.type
        if type == "main":
            subcomponent_student = Student.objects.filter(student_mappings__course__in = course , student_mappings__batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ,  dropped = False , is_archived =  False , user__is_active = True).distinct()
        else:
            subcomponent_student = Student.objects.filter(resets__batch=batch,resets__term=term,resets__course__in=course , resets__type= type , resets__subjects = subcomponent.component.subject_mapping.id ,  dropped = False , is_archived =  False , user__is_active = True).distinct()
        student_serializer = StudentMixSerializer(subcomponent_student , many = True)
        student_marks = { mark.student.id : mark.obtained_marks for mark in SubComponentMarks.objects.filter(subcomponent = subcomponent_id)}
        for student in student_serializer.data:
            student['marks'] = student_marks.get(student['id'] , 00)
            if subcomponent.is_submission:
                if SubComponentAnswers.objects.filter(student=student["id"],sub_component=subcomponent_id).exists():
                    student["submitted"] = True
                else:
                    student["submitted"]  = False
            else:
                student["submitted"] = True
        message = "sub component student list fetch successfully"
        return response_handler(message=message , code = 200 , data=student_serializer.data , extra={'max_marks':subcomponent.max_marks})
    
    def post(self,request , subcomponent_id):
        subcomponent = get_object_or_404(SubComponent , id = subcomponent_id)
        course = subcomponent.component.subject_mapping.course.all()
        batch = subcomponent.component.subject_mapping.batch
        term =  subcomponent.component.subject_mapping.term
        specialization= subcomponent.component.subject_mapping.specialization.all()
        type = subcomponent.component.subject_mapping.type
        if type == "main":
            subcomponent_student = Student.objects.filter(student_mappings__course__in = course , student_mappings__batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ,  dropped = False , is_archived =  False , user__is_active = True).distinct().values_list('id' , flat=True)
        else:
            subcomponent_student = Student.objects.filter(resets__batch=batch,resets__term=term,resets__course__in=course , resets__type= type , resets__subjects = subcomponent.component.subject_mapping.id ,  dropped = False , is_archived =  False , user__is_active = True).distinct().values_list('id' , flat=True)
        marks_objects = request.data.get('marks_student' , [])
        student_get_id = [marks_object['id'] for marks_object in marks_objects]
        if not set(student_get_id).issubset(set(subcomponent_student)):
            return response_handler(message= "Some students do not belong to this class" , code = 400 , data={})
        student_get_marks = [marks_object['marks'] for marks_object in marks_objects]
        if any(std_mark > subcomponent.max_marks for std_mark in student_get_marks):
            return response_handler(message= "marks of student is equal and less then max marks of subcomponent" , code = 400 , data= {})
        for marks_object in marks_objects:
            std = get_object_or_404(Student , id = marks_object['id'])
            SubComponentMarks.objects.update_or_create(subcomponent = subcomponent,
                                    student = std , 
                                    defaults={'obtained_marks': marks_object['marks']})
        message = "Sub Component marks uploaded successfully."
        return response_handler(message = message , code = 200 , data = {})
    

class ComponentAnswersPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message': 'Component Answer no found' , 'code':400 , 'data':{} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Component Answer list fetched successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra':{'count':total_items , 'total':total_page , 'page_size':self.page_size}})



class ComponentAnswersModelViewSet(viewsets.ModelViewSet):
    queryset = ComponentAnswers.objects.all().order_by('-id')
    serializer_class = ComponentAnswersSerializer
    pagination_class = ComponentAnswersPagination
    http_method_names = ['get' , 'post' , 'delete' , 'put']
    filter_backends = [DjangoFilterBackend , SearchFilter]
    filterset_fields = []

    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Component Answers no found"
            return response_handler(message= message , code = 400 , data = {})
    
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Component Answers create successfully"
            return response_handler(message  = message , code = 200 , data = response.data)
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
        message = "Component Answers data retrived successfully"
        return response_handler(message= message , code = 200 , data=serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance , data = request.data ,partial = True )
        if serializer.is_valid():
            serializer.save()
            message = "Component Answers updated successfully"
            return response_handler(message = message , code = 200  , data = serializer.data)
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message = message , code = 400 , data = {})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Component Answers deleted successfully"
            return response_handler(message = message , code = 200 , data = {})
        except:
            message = "Component Answers no found"
            return response_handler(message=message , code = 400 , data= {})
        



class SubComponentAnswersPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message': 'Sub Component Answer no found' , 'code':400 , 'data':{} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Sub Component Answer list fetched successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra':{'count':total_items , 'total':total_page , 'page_size':self.page_size}})



class SubComponentAnswersModelViewSet(viewsets.ModelViewSet):
    queryset = SubComponentAnswers.objects.all().order_by('-id')
    serializer_class = SubComponentAnswersSerializer
    pagination_class = SubComponentAnswersPagination
    http_method_names = ['get' , 'post' , 'delete' , 'put']
    filter_backends = [DjangoFilterBackend , SearchFilter]
    filterset_fields = []

    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Sub Component Answers no found"
            return response_handler(message= message , code = 400 , data = {})
    
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Sub Component Answers create successfully"
            return response_handler(message  = message , code = 200 , data = response.data)
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
        message = "Sub Component Answers data retrived successfully"
        return response_handler(message= message , code = 200 , data=serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance , data = request.data ,partial = True )
        if serializer.is_valid():
            serializer.save()
            message = "Sub Component Answers updated successfully"
            return response_handler(message = message , code = 200  , data = serializer.data)
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message = message , code = 400 , data = {})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Sub Component Answers deleted successfully"
            return response_handler(message = message , code = 200 , data = {})
        except:
            message = "Sub Component Answers no found"
            return response_handler(message=message , code = 400 , data= {})
        

# student marks subject mapping wise 

class ComponentMarksSubjectWiseSummary(APIView):
    def get(self, request, student_id, subject_id):
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(SubjectMapping, id=subject_id)
        
        components = Component.objects.filter(subject_mapping=subject)
        component_marks_list = []
        
        for component in components:
            component_mark = ComponentMarks.objects.filter(component=component, student=student).first()
            if component_mark:
                mark = component_mark.obtained_marks
            else:
                mark = "Not Marked"

            if component.has_subcomponents:
                sub_components = SubComponent.objects.filter(component=component)
                subcomponent_marks_list = []
                for sub_component in sub_components:
                    sub_component_mark = SubComponentMarks.objects.filter(subcomponent=sub_component, student=student).first()
                    if sub_component_mark:
                        mark = sub_component_mark.obtained_marks
                    else:
                        mark = "Not Marked"

                    subcomponent_marks_list.append({
                        'sub_component' : sub_component.name,
                        'out_of_sub_marks':sub_component.max_marks,
                        'sub_marks':mark
                    })
            else:
                subcomponent_marks_list = "its no have sub component"

            component_marks_list.append({
                'component': component.name,
                'out_of_marks':component.max_marks,  # Assuming Component has a name field
                'marks': mark,
                'subcomponent_marks_list':subcomponent_marks_list
            })
        
        return response_handler(message = "Student marks fetched successfully" , code = 200 , data = { 'component_marks': component_marks_list})



class SubcomponentViewUpdateAPIView(APIView):
    def get(self, request , sub_component_id):
        sub_component = get_object_or_404(SubComponent , id = sub_component_id)
        sub_component = SubComponentMixListSerializer(sub_component)
        return response_handler(message="sub component data retrived successfully"  , code = 200 , data = sub_component.data)
    
    def put(self, request , sub_component_id):
        sub_component = get_object_or_404(SubComponent , id = sub_component_id)
        serializer = SubComponentSerializer(sub_component , data = request.data ,partial = True )
        if serializer.is_valid():
            serializer.save()
            message = "Sub Component updated successfully"
            return response_handler(message = message , code = 200  , data = serializer.data)
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message = message , code = 400 , data = {})
        




class StudentComponentAnswer(APIView):
    def get(self, request , component_id):
        component = get_object_or_404(Component , id = component_id)
        course = component.subject_mapping.course.all()
        batch = component.subject_mapping.batch
        term =  component.subject_mapping.term
        specialization= component.subject_mapping.specialization.all()
        type = component.subject_mapping.type
        if type == "main":
            component_student = Student.objects.filter(student_mappings__course__in = course , student_mappings__batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization , dropped = False , is_archived =  False , user__is_active = True).distinct()
        else:
            component_student = Student.objects.filter(resets__batch_id=batch,resets__term_id=term,resets__course__in=course , resets__type= type , resets__subjects_id = component.subject_mapping.id ,  dropped = False , is_archived =  False , user__is_active = True).distinct()
        students_data = []
        for student in component_student:
            one_student =  StudentMixSerializer(student).data
            if ComponentAnswers.objects.filter(student=student,component_id=component_id).exists():
                one_student["submitted"] = True
            else:
                one_student["submitted"]  = False
            students_data.append(one_student)
        return response_handler(message="student answer list fetched successfully" , code= 200 , data = students_data)
    

class StudentComponentAnswerDetails(APIView):
    def get(self, request, student_id, component_id):
        answer = ComponentAnswers.objects.filter(student_id=student_id, component_id=component_id).first()
        if not answer:
            return response_handler(message="Answer not found", code=404, data={})

        answer = ComponentAnswersSerializer(answer)
        return response_handler(message="Answer data fetched successfully", code=200, data=answer.data)

    def post(self, request, student_id, component_id):
        data = request.data.copy()
        # Add student_id and component_id to the request data
        data['student'] = student_id
        data['component'] = component_id
        
        # Check if the record already exists
        existing_answer = ComponentAnswers.objects.filter(student_id=student_id, component_id=component_id).first()
        if existing_answer:
            # Update the existing record
            serializer = ComponentAnswersSerializer(existing_answer, data=data, partial=True)  # partial=True for partial updates
            if serializer.is_valid():
                serializer.save()  # This will update the existing record
                return response_handler(message="Answer updated successfully", code=200, data=serializer.data)
            return response_handler(message=format_serializer_errors(serializer.errors)[0], code=400, data={})
        else:
            # Create a new record
            serializer = ComponentAnswersSerializer(data=data)
            if serializer.is_valid():
                serializer.save()  # This will create the new record
                return response_handler(message="Answer created successfully", code=201, data=serializer.data)
            return response_handler(message=format_serializer_errors(serializer.errors)[0], code=400, data={})



class StudentSubComponentAnswer(APIView):
    def get(self, request , subcomponent_id):
        subcomponent = get_object_or_404(SubComponent , id = subcomponent_id)
        course = subcomponent.component.subject_mapping.course.all()
        batch = subcomponent.component.subject_mapping.batch
        term =  subcomponent.component.subject_mapping.term
        specialization= subcomponent.component.subject_mapping.specialization.all()
        type = subcomponent.component.subject_mapping.type
        if type == "main":
            subcomponent_student = Student.objects.filter(student_mappings__course__in = course , student_mappings__batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ,  dropped = False , is_archived =  False , user__is_active = True ).distinct()
        else:
            subcomponent_student = Student.objects.filter(resets__batch_id=batch,resets__term_id=term,resets__course__in=course , resets__type= type  , resets__subjects_id = subcomponent.component.subject_mapping.id ,  dropped = False , is_archived =  False , user__is_active = True).distinct()
        students_data = []
        for student in subcomponent_student:
            one_student =  StudentMixSerializer(student).data
            if SubComponentAnswers.objects.filter(student=student,sub_component=subcomponent_id).exists():
                one_student["submitted"] = True
            else:
                one_student["submitted"]  = False
            students_data.append(one_student)
        return response_handler(message="student answer list fetched successfully" , code= 200 , data = students_data)





class StudentSubComponentAnswerDetails(APIView):
    def get(self, request, student_id, subcomponent_id):
        answer = SubComponentAnswers.objects.filter(student_id=student_id, sub_component_id=subcomponent_id).first()
        if not answer:
            return response_handler(message="Answer not found", code=404, data={})
        
        answer = SubComponentAnswersSerializer(answer)
        return response_handler(message="Answer data fetched successfully", code=200, data=answer.data)

    def post(self, request, student_id, subcomponent_id):
        data = request.data.copy()
        # Add student_id and subcomponent_id to the request data
        data['student'] = student_id
        data['sub_component'] = subcomponent_id
        
        # Check if the record already exists
        existing_answer = SubComponentAnswers.objects.filter(student_id=student_id, sub_component_id=subcomponent_id).first()
        if existing_answer:
            # Update the existing record
            serializer = SubComponentAnswersSerializer(existing_answer, data=data, partial=True)  # partial=True for partial updates
            if serializer.is_valid():
                serializer.save()  # This will update the existing record
                return response_handler(message="Answer updated successfully", code=200, data=serializer.data)
            return response_handler(message=format_serializer_errors(serializer.errors)[0], code=400, data={})
        else:
            # Create a new record
            serializer = SubComponentAnswersSerializer(data=data)
            if serializer.is_valid():
                serializer.save()  # This will create the new record
                return response_handler(message="Answer created successfully", code=201, data=serializer.data)
            return response_handler(message=format_serializer_errors(serializer.errors)[0], code=400, data={})



class SubjectWiseComponentMarksAPIView(APIView):
    def get(self, request, subject_id):
        components = Component.objects.filter(subject_mapping=subject_id).order_by('-id')
        if not components.exists():
            return response_handler(message="No components found", code=404, data={})

        subject_mapping = components.first().subject_mapping
        course = subject_mapping.course.all()
        batch = subject_mapping.batch
        term = subject_mapping.term
        specialization = subject_mapping.specialization.all()
        type = subject_mapping.type

        if type == "main":
            students = Student.objects.filter(
                student_mappings__course__in=course,
                student_mappings__batch=batch,
                student_mappings__term=term,
                student_mappings__specialization__in=specialization
            ).distinct()
        else:
            students = Student.objects.filter(
                resets__batch=batch,
                resets__term=term,
                resets__course__in=course,
                resets__type=type,
                resets__subjects=subject_mapping.id
            ).distinct()

        student_serializer = StudentAttendanceSerializer(students, many=True)
        student_data = {s['id']: s for s in student_serializer.data}

        # Initialize marks dictionary for each student
        for student in student_data.values():
            student['component_marks'] = []

        # For each component, assign marks to students
        for component in components:
            marks = ComponentMarks.objects.filter(component=component)
            mark_map = {m.student.id: m.obtained_marks for m in marks}

            for student_id, student in student_data.items():
                student['component_marks'].append({
                    'component_id': component.id,
                    'component_name': component.name,
                    'obtained_marks': mark_map.get(student_id, 0),
                    'max_marks': component.max_marks,
                })

        return response_handler(
            message="Component marks fetched successfully",
            code=200,
            data=list(student_data.values())
        )
