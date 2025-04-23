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
            code=status.HTTP_200_OK,
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
        student_serializer = StudentAttendanceSerializer(instance = students , many = True)
        student_attendance = {attendance.student.id : {"is_persent": attendance.is_persent, "ce_marks": attendance.ce_marks} for attendance in Attendance.objects.filter(class_schedule = class_id)}
        for student in student_serializer.data:
            
            student_info = student_attendance.get(student['id'] , {})
            student['is_persent'] = student_info.get("is_persent", True)
            student['ce_marks'] = student_info.get("ce_marks", 0)
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
        student_class_info = request.data.get("student_class_info" ,[])
        student_class_info_dict = {item['id'] : {"is_persent": item['is_persent'] , "ce_marks": item['ce_marks']} for item in student_class_info}
        is_valid = set(student_class_info_dict.keys()).issubset(set(students.values_list('id' , flat=True)))
        if not is_valid:
            return response_handler(message="Some students do not belong to this class." , code = 400 , data= {})
        attendance_records = []
        for student in students:
            student_info = student_class_info_dict.get(student.id, {})
            # import pdb; pdb.set_trace()
            is_persent = student_info.get("is_persent")
            ce_marks = student_info.get("ce_marks")
            attendance , created = Attendance.objects.get_or_create(
                class_schedule = class_schedule , 
                student = student,
                defaults= {'is_persent' : is_persent , 'ce_marks':ce_marks})
            if not created:
                attendance.is_persent = is_persent
                attendance.ce_marks = ce_marks
                attendance.save()
            attendance_records.append({
                "student_id" : student.id , 
                "is_persent" :is_persent , 
                "ce_marks":ce_marks
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
            specialization__in=student_mappings.values_list("specialization", flat=True),
            is_active = True, # there is_active true for current term subject show 
            type = "main"
        )
        resit_subjects = SubjectMapping.objects.filter(
            resets__student=student,
            is_active = True).distinct() ## for  requested resit subject
        
        subject_mappings = subject_mappings.union(resit_subjects)
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
            attended_classes  = Attendance.objects.filter(class_schedule__mapping =   subject_mapping , student = student.id , is_persent = True).count()
            complete_classes = subject_mapping.classes_completed
            attended_percentage = (attended_classes /complete_classes)*100 if complete_classes > 0 else 0
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
                "attendance": subject_attendance ,
                "attended_percentage" : attended_percentage
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
        
        if not term:
            subject_mappings = subject_mappings.filter(is_active = True)  # there is active for current subject

        filters = Q()
        if mapping:
            filters &= Q(pk=mapping)
        if term:
            filters &= Q(term=term)
        subject_mappings = subject_mappings.filter(filters)
        if not subject_mappings.filter(filters).exists():
            return response_handler(message="this subject still not assign you" , code = 200  , data = {})
        # import pdb; pdb.set_trace()
        
        # Date parsing
        if s_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
        if e_date:
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()

        class_schedules = ClassSchedule.objects.filter(
            mapping__in=subject_mappings,
            is_cancel=False,
            is_complete=True
        )

        # Apply date filters only if provided
        if s_date and e_date:
            class_schedules = class_schedules.filter(date__range=[s_date, e_date])
        elif s_date:
            class_schedules = class_schedules.filter(date=s_date)
        elif e_date:
            class_schedules = class_schedules.filter(date=e_date)

        attendance_records = Attendance.objects.filter(
            student=student,
            class_schedule__in=class_schedules
        )

        # If no date range provided, use full date range from schedules for summary loop
        if not s_date and not e_date and class_schedules.exists():
            s_date = class_schedules.order_by("date").first().date
            e_date = class_schedules.order_by("-date").first().date

        # Generate attendance summary
        attendance_summary = []
        for subject_mapping in subject_mappings:
            attended_classes  = Attendance.objects.filter(class_schedule__mapping =   subject_mapping , student = student.id , is_persent = True).count()
            complete_classes = subject_mapping.classes_completed
            attended_percentage = (attended_classes /complete_classes)*100 if complete_classes > 0 else 0
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
                "attendance": subject_attendance , 
                "attended_percentage" : attended_percentage
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
            type = "main",
            is_active = True,
            specialization__in=student_mappings.values_list("specialization", flat=True)
        )
        resit_subjects = SubjectMapping.objects.filter(
            resets__student=student,
            is_active = True).distinct() # for requested resit subject

        # Combine both regular and resit subject mappings
        combined_subjects = subject_mappings.union(resit_subjects)
        filters = Q()
        if mapping:
            filters &= Q(pk=mapping)
        if term:
            filters &= Q(term=term)
        subject_mappings = combined_subjects.filter(filters)

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
    


class UpComingFacultyClassAPIView(APIView):
    def get(self, request, faculty_id):
        mapping_ids = request.query_params.getlist('mapping')  # Use getlist for multiple values
        term = request.query_params.get('term')
        s_date = request.query_params.get('s_date')
        e_date = request.query_params.get('e_date')

        faculty = get_object_or_404(Employee, id=faculty_id)
        class_schedules = ClassSchedule.objects.filter(mapping__faculty=faculty)
        if not term:
            class_schedules = class_schedules.filter(mapping__is_active=True)  # there is active for current subject
        filters = Q()
        if mapping_ids:
            filters &= Q(mapping__in=mapping_ids)
        if term:
            filters &= Q(mapping__term=term)

        class_schedules = class_schedules.filter(filters)

        # Date filter
        if s_date and e_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
        elif s_date:
            s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            e_date = s_date
        elif e_date:
            e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
            s_date = e_date
        else:
            s_date = e_date = None

        if s_date or e_date:
            class_schedules = class_schedules.filter(date__range=[s_date, e_date])

        # Order and serialize
        class_schedules = class_schedules.order_by('-date')
        class_schedules = ClassScheduledListSerializer(class_schedules, many=True)
        return response_handler(message = "upcoming class fetched successfully"  ,code = 200  ,  data = class_schedules.data )
    



class UpComeingSubjectMappingClassAPIView(APIView):
    def get(self, request, subject_id):
        term = request.query_params.get('term')
        s_date = request.query_params.get('s_date')
        e_date = request.query_params.get('e_date')
        subject_id = get_object_or_404(SubjectMapping , id = subject_id)
        today = datetime.today().date()
        class_schedules = ClassSchedule.objects.filter(
            mapping = subject_id
            ).order_by('-date')
        filters = Q()
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
    


