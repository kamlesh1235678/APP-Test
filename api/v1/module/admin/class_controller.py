from rest_framework import viewsets
from modules.administration.models import *
from modules.users.models import *
from api.v1.module.serializers.class_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from api.v1.module.response_handler import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from api.v1.module.serializers.student_serializer import *
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.utils.dateparse import parse_date, parse_time
from django.utils.decorators import method_decorator
from api.v1.module.admin.decorator import *
from datetime import datetime, timedelta
from django.db.models import Q


class ClassScheduledPagination(PageNumberPagination):
    page_size = 10 
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Class Scheduled no found' , 'code':400 , 'data': {} , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Class Scheduled list fetch successfully"
        return Response({'message':message , 'code':200 , 'data':data , 'extra': {'count':total_items , 'total': total_page , 'page_size': self.page_size}})


import django_filters

class ClassFilter(django_filters.FilterSet):
    s_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    e_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = ClassSchedule
        fields = ['mapping__term', 'mapping', 's_date', 'e_date']

class ClassScheduledModelViewSet(viewsets.ModelViewSet):
    queryset = ClassSchedule.objects.all().order_by('-id')
    serializer_class = ClassScheduledSerializer
    pagination_class = ClassScheduledPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends = [SearchFilter , DjangoFilterBackend]
    filterset_class = ClassFilter
    filterset_fields = ['date' , 'mapping' , "mapping__term"]


    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ClassScheduledListSerializer
        return ClassScheduledSerializer


    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Class Scheduled lsit fetch successfully"
            return response_handler(message=message, code=400 , data= {})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Class Scheduled create successfully"
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
        date_str = request.data['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.today().date()
        if date < today:
            return response_handler(message="Back Date Class not schedule" , code = 400 , data = {})
        serializer = self.serializer_class(instance , data = request.data , partial = True)
        if serializer.is_valid():
            serializer.save()
            message = "Class Scheduled updated successfully"
            return response_handler(message= message , code = 200 , data = serializer.data )
        message = format_serializer_errors(serializer.errors)[0]
        return response_handler(message=message , code= 400 , data= {})
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        message = "Class Scheduled data retrived successfully"
        return response_handler(message= message , code= 200 , data=serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            Attendance.objects.filter(class_schedule=instance.pk).delete()
            self.perform_destroy(instance)
            message = "Class Scheduled delete successfully"
            return response_handler(message= message , code = 200 , data= {})
        except:
            message = "Class Scheduled no found"
            return response_handler(message= message , code = 400 , data= {})
        
    @action(detail=True , methods=['post'])
    def cancel(self, request , pk = None):
        instance = self.get_object()
        if instance.is_complete:
            return response_handler(message = "Class already completed" , code = 400  , data = {})
        if instance.is_cancel:
            instance.is_cancel = False  
            instance.save()
            message = "Class rescheduled successfully"
        else:
            instance.is_cancel = True  
            instance.save()
            message = "Class canceled successfully"
        return response_handler(message= message , code = 200 , data = {})
        
class BulkClassScheduledAPIView(APIView):
    def post(self, request):
        schedules_data = request.data.get("schedules", [])
        
        if not schedules_data:
            return response_handler("No schedules provided", status.HTTP_400_BAD_REQUEST, {})
        
        created_schedules = []
        errors = []
        
        for schedule in schedules_data:
            mapping_id = schedule.get("mapping")
            date = schedule.get("date")
            start_time = schedule.get("start_time")
            end_time = schedule.get("end_time")
            
            if not all([mapping_id, date, start_time, end_time]):
                errors.append({"error": "Missing required fields", "data": schedule})
                continue
            
            try:
                class_schedule = ClassSchedule.objects.create(
                    mapping_id=mapping_id,
                    date=parse_date(date),
                    start_time=parse_time(start_time),
                    end_time=parse_time(end_time)
                )
                created_schedules.append(ClassScheduledSerializer(class_schedule).data)
            except Exception as e:
                errors.append({"error": str(e), "data": schedule})
        
        return response_handler(
            message="Classes scheduled successfully",
            code=status.HTTP_201_CREATED,
            data={"created": created_schedules, "errors": errors}
        )

class ClassAttendanceAPIView(APIView):
    # @method_decorator(validate_attendance_time, name='dispatch')
    def get(self, request , class_id):
        class_schedule = get_object_or_404(ClassSchedule , id = class_id)
        course = class_schedule.mapping.course.all()
        batch = class_schedule.mapping.batch
        term =  class_schedule.mapping.term
        specialization= class_schedule.mapping.specialization.all()
        students = Student.objects.filter(course__in = course , batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ).distinct()
        student_serializer = StudentMixSerializer(instance = students , many = True)
        student_attendance = {attendance.student.id : attendance.is_persent for attendance in Attendance.objects.filter(class_schedule = class_id)}
        for student in student_serializer.data:
            student['is_persent'] = student_attendance.get(student['id'] , True)
        message = "class wise student list fetch successfully"
        data = {
            "class_schedule": ClassScheduledListSerializer(class_schedule).data,
            "students": student_serializer.data,}
        return response_handler(message = message , code = 200  , data = data)
    

    # @method_decorator(validate_attendance_time, name='dispatch')
    def post(self, request , class_id):
        class_schedule = get_object_or_404(ClassSchedule , id = class_id)
        course = class_schedule.mapping.course.all()
        batch = class_schedule.mapping.batch
        term =  class_schedule.mapping.term
        specialization= class_schedule.mapping.specialization.all()
        students = Student.objects.filter(course__in = course , batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ).distinct()
        persent_student_id = request.data.get("present_students" ,[])
        is_valid = set(persent_student_id).issubset(set(students.values_list('id' , flat=True)))
        if not is_valid:
            return response_handler(message="Some students do not belong to this class." , code = 400 , data= {})
        attendance_records = []
        for student in students:
            is_persent = student.id in persent_student_id
            attendance , created = Attendance.objects.get_or_create(
                class_schedule = class_schedule , 
                student = student,
                defaults= {'is_persent' : is_persent})
            if not created:
                attendance.is_persent = is_persent
                attendance.save()
            attendance_records.append({
                "student_id" : student.id , 
                "is_persent" :is_persent
            })

        class_schedule.is_complete = True
        class_schedule.save()

        return response_handler(message = "Attendance Mark successfully"  , code = 200 , data = attendance_records)
    

class SubjectAttendanceListAPIView(APIView):
    def get(self, request , subject_mapping_id):
        mapping_subject =  get_object_or_404(SubjectMapping , id = subject_mapping_id)
        attendance = Attendance.objects.filter( class_schedule__mapping =   mapping_subject)
        students = Student.objects.filter(course__in = mapping_subject.course.all() , batch = mapping_subject.batch , student_mappings__term = mapping_subject.term , student_mappings__specialization__in = mapping_subject.specialization.all() ).distinct()
        students_serializer = StudentSerializer(students , many = True)
        complete_classes = mapping_subject.classes_completed
        for student in students_serializer.data:
            attended_classes  = attendance.filter(student = student['id'] , is_persent = True).count()
            attended_percentage = (attended_classes /complete_classes)*100 if complete_classes > 0 else 0
            student['attendance_percentage'] = attended_percentage

        message = "Student List fetched successfully"
        return response_handler(message= message , code = 200 , data=students_serializer.data)



class AttendanceSummary(APIView):
    def get(self, request, student_id, days):
        try:
            days = int(days)
            if days not in [7, 15]:
                return response_handler(message="Invalid days. Only 7 or 15 allowed.", code=400, data={})
        except ValueError:
            return response_handler(message="Days parameter must be an integer.", code=400, data={})
        
        today = datetime.today().date()
        start_date = today - timedelta(days=days - 1)
        student = get_object_or_404(Student, id=student_id)
        student_mappings = StudentMapping.objects.filter(student=student)
        
        # Step 1: Get student's subjects
        subject_mappings = SubjectMapping.objects.filter(
            batch=student.batch,
            course=student.course,
            term__in=student_mappings.values_list("term", flat=True),
            specialization__in=student_mappings.values_list("specialization", flat=True)
        )
        
        # Step 2: Get class schedules for the subjects in the last 'days'
        class_schedules = ClassSchedule.objects.filter(
            date__range=[start_date, today],
            mapping__in=subject_mappings,
            is_cancel=False,
            is_complete=True
        )
        
        # Step 3: Get attendance records
        attendance_records = Attendance.objects.filter(
            student=student,
            class_schedule__in=class_schedules
        )
        
        # Generate attendance summary
        attendance_summary = []
        for subject_mapping in subject_mappings:
            subject_attendance = []
            for i in range(days):
                current_date = today - timedelta(days=i)
                class_schedule = class_schedules.filter(date=current_date, mapping=subject_mapping).first()
                
                if class_schedule:
                    attendance = attendance_records.filter(class_schedule=class_schedule).first()
                    status = "Present" if attendance and attendance.is_persent else "Absent"
                else:
                    status = "Class Not Scheduled"
                
                subject_attendance.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "status": status
                })
            
            attendance_summary.append({
                "subject_mapping": SubjectMappingListSerializer(subject_mapping).data,
                "attendance": subject_attendance
            })
        
        return response_handler(message="Summary fetched successfully", code=200, data=attendance_summary)





            

class AttendanceSummaryFilter(APIView):
    def get(self, request, student_id):
        mapping = request.query_params.get('mapping')
        term = request.query_params.get('term')
        s_date = request.query_params.get('s_date')
        e_date = request.query_params.get('e_date')

        student = get_object_or_404(Student, id=student_id)
        student_mappings = StudentMapping.objects.filter(student=student)

        # Get student's subjects
        subject_mappings = SubjectMapping.objects.filter(
            batch=student.batch,
            course=student.course,
            term__in=student_mappings.values_list("term", flat=True),
            specialization__in=student_mappings.values_list("specialization", flat=True)
        )

        filters = Q()
        if mapping:
            filters &= Q(pk=mapping)
        if term:
            filters &= Q(term=term)
        subject_mappings = subject_mappings.filter(filters)
        if not subject_mappings.filter(filters).exists():
            return response_handler(message="this subject still not assign you" , code = 200  , data = {})
        # import pdb; pdb.set_trace()
        
        # filters1 = Q()
        # Determine date range
        today = datetime.today().date()
        if s_date and e_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
        elif s_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = s_date  # If only start date is given, consider attendance for that date only
        elif e_date:
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
            s_date = e_date  # If only end date is given, consider attendance for that date only
        else:
            e_date = today
            s_date = today - timedelta(days=6)  # Default last 7 days

        # filters1 &= Q(date__gte=s_date, date__lte=e_date)

        # Get class schedules
        class_schedules = ClassSchedule.objects.filter(
            mapping__in=subject_mappings,
            is_cancel=False,
            is_complete=True,
            date__range=[s_date, e_date]
        )

        # Get attendance records
        attendance_records = Attendance.objects.filter(
            student=student,
            class_schedule__in=class_schedules
        )

        # Generate attendance summary
        attendance_summary = []
        for subject_mapping in subject_mappings:
            subject_attendance = []
            days = (e_date - s_date).days + 1  # Calculate total days in the range

            for i in range(days):
                current_date = s_date + timedelta(days=i)
                class_schedule = class_schedules.filter(date=current_date, mapping=subject_mapping).first()

                if class_schedule:
                    attendance = attendance_records.filter(class_schedule=class_schedule).first()
                    status = "Present" if attendance and attendance.is_persent else "Absent"
                else:
                    status = "Class Not Scheduled"

                subject_attendance.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "status": status
                })

            attendance_summary.append({
                "subject_mapping": SubjectMappingListSerializer(subject_mapping).data,
                "attendance": subject_attendance
            })

        return response_handler(message="Summary fetched successfully", code=200, data=attendance_summary)




            


class UpComeingStudentClassAPIView(APIView):
    def get(self, request, student_id):
        mapping = request.query_params.get('mapping')
        term = request.query_params.get('term')
        s_date = request.query_params.get('s_date')
        e_date = request.query_params.get('e_date')
        student = get_object_or_404(Student, id=student_id)
        student_mappings = StudentMapping.objects.filter(student=student)
        
        # Step 1: Get student's subjects
        subject_mappings = SubjectMapping.objects.filter(
            batch=student.batch,
            course=student.course,
            term__in=student_mappings.values_list("term", flat=True),
            specialization__in=student_mappings.values_list("specialization", flat=True)
        )
        filters = Q()
        if mapping:
            filters &= Q(pk=mapping)
        if term:
            filters &= Q(term=term)
        subject_mappings = subject_mappings.filter(filters)

        today = datetime.today().date()
        
        if s_date and e_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
            class_schedules = ClassSchedule.objects.filter(
            mapping__in=subject_mappings,
            date__range=[s_date, e_date]
            )
        elif s_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = s_date
            class_schedules = ClassSchedule.objects.filter(
            mapping__in=subject_mappings,
            date__range=[s_date, e_date]
            )  
        elif e_date:
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
            s_date = e_date  
            class_schedules = ClassSchedule.objects.filter(
            mapping__in=subject_mappings,
            date__range=[s_date, e_date]
            )
        else:
            class_schedules = ClassSchedule.objects.filter(
            mapping__in=subject_mappings,
            date__gte = today
            )
        

        
        class_schedules =  ClassScheduledListSerializer(class_schedules , many = True)
        return response_handler(message = "upcoming class fetched successfully"  ,code = 200  ,  data = class_schedules.data )
    


class UpComeingFacultyClassAPIView(APIView):
    def get(self, request, faculty_id):
        mapping = request.query_params.get('mapping')
        term = request.query_params.get('term')
        s_date = request.query_params.get('s_date')
        e_date = request.query_params.get('e_date')
        faculty_id = get_object_or_404(Employee , id = faculty_id)
        today = datetime.today().date()
        class_schedules = ClassSchedule.objects.filter(
            mapping__faculty = faculty_id
            ).order_by('-date')
        filters = Q()
        if mapping:
            filters &= Q(mapping__in=mapping)
        if term:
            filters &= Q(mapping__term=term)
        class_schedules = class_schedules.filter(filters)
        if s_date and e_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
            class_schedules = class_schedules.filter(
            date__range=[s_date, e_date]
            )
        elif s_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = s_date
            class_schedules = class_schedules.filter(
            date__range=[s_date, e_date]
            )  
        elif e_date:
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
            s_date = e_date  
            class_schedules = class_schedules.filter(
            date__range=[s_date, e_date]
            )
        else:
            class_schedules = class_schedules

        
        class_schedules =  ClassScheduledListSerializer(class_schedules , many = True)
        return response_handler(message = "upcoming class fetched successfully"  ,code = 200  ,  data = class_schedules.data )