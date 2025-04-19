from modules.administration.models import *
from api.v1.module.serializers.mix_serializer import *
from api.v1.module.serializers.class_serializer import *
from rest_framework.response import Response
from api.v1.module.response_handler import *
from django.core.mail import send_mass_mail
from django.conf import settings
import time
import logging
from django.db.models import Q
from datetime import datetime
from api.v1.module.serializers.exam_serializer import *
from api.v1.module.serializers.employee_serializer import *

# Configure logging
logger = logging.getLogger(__name__)

def send_bulk_emails(email_list, subject, message):
    batch_size=50
    delay=1
    if not email_list:
        return {"message": "No valid email addresses provided", "code": 200, "data": {}}

    total_sent = 0
    total_emails = len(email_list)
    email_batches = [email_list[i:i+batch_size] for i in range(0, total_emails, batch_size)]

    for batch in email_batches:
        email_messages = [(subject, message, settings.DEFAULT_FROM_EMAIL, [email]) for email in batch]
        import pdb;pdb.set_trace()
        try:
            send_mass_mail(email_messages, fail_silently=False)
            total_sent += len(batch)
            logger.info(f"Sent {len(batch)} emails successfully.")
        except Exception as e:
            logger.error(f"Failed to send batch: {str(e)}")

        time.sleep(delay)  # Avoid hitting SES rate limits

    return {"message": f"Emails sent to {total_sent} recipients.", "code": 200}



#         send_bulk_emails(
#         subject="Test Email from AWS SES",
#         message="This is a test email from taxila.in using AWS SES SMTP.",
#         email_list=["punnet@taxila.com" , "98kamleshkumawat@gmail.com"]
#     )


class MixAPIView(APIView):
    def get(self, request):
        batch = Batch.objects.filter(is_active = True).order_by('-id')
        terms = Terms.objects.filter(is_active = True).order_by('-id')
        course = Course.objects.filter(is_active = True).order_by('-id')
        subject = Subject.objects.filter(is_active = True).order_by('-id')
        specialization = Specialization.objects.filter(is_active = True).order_by('-id')

        data = {
            "batches": BatchMixSerializer(batch, many=True).data,
            "terms": TermsMixSerializer(terms, many=True).data,
            "courses": CourseMixSerializer(course, many=True).data,
            "subjects": SubjectMixSerializer(subject, many=True).data,
            "specializations": SpecializationMixSerializer(specialization, many=True).data,
        }

        return response_handler(message="List fetched successfully", code=200, data=data )
    

class BatchSingleListAPIView(APIView):
    def get(self, request):
        batches = Batch.objects.filter(is_active = True).order_by('-id')
        return Response({"message": "Batches fetched successfully", "data": BatchMixSerializer(batches, many=True).data})

class TermsSingleListAPIView(APIView):
    def get(self, request):
        terms = Terms.objects.filter(is_active = True).order_by('-id')
        return Response({"message": "Terms fetched successfully", "data": TermsMixSerializer(terms, many=True).data})

class CourseSingleListAPIView(APIView):
    def get(self, request):
        courses = Course.objects.filter(is_active = True).order_by('-id')
        return Response({"message": "Courses fetched successfully", "data": CourseMixSerializer(courses, many=True).data})

class SubjectSingleListAPIView(APIView):
    def get(self, request):
        subjects = Subject.objects.filter(is_active = True).order_by('-id')
        return Response({"message": "Subjects fetched successfully", "data": SubjectMixSerializer(subjects, many=True).data})

class SpecializationSingleListAPIView(APIView):
    def get(self, request):
        specializations = Specialization.objects.filter(is_active = True).order_by('-id')
        return Response({"message": "Specializations fetched successfully", "data": SpecializationMixSerializer(specializations, many=True).data})


class SubjectMappingSingleListAPIView(APIView):
    def get(self, request):
        term = request.query_params.get('term')
        specialization = request.query_params.get('specialization')
        course = request.query_params.get('course')
        batch = request.query_params.get('batch')
        type_value = request.query_params.get('type')  
        faculty = request.query_params.get('faculty') 
        is_active =  request.query_params.get('is_active') 

        filters = Q()
        if term:
            filters &= Q(term_id=term)
        if specialization:
            filters &= Q(specialization__id=specialization)
        if course:
            filters &= Q(course__id=course)
        if batch:
            filters &= Q(batch_id=batch)
        if type_value:
            filters &= Q(type=type_value)
        if faculty:
            filters &= Q(faculty=faculty)
        if is_active:
            filters &= Q(batch__is_active = is_active)


        subject_mapping = SubjectMapping.objects.filter(filters).distinct().order_by('-id')

        return Response({
            "message": "Subject mappings fetched successfully",
            "data": SubjectMappingMixSerializer(subject_mapping, many=True).data
        })
    

class ComponentFilterAPIView(APIView):
    def get(self, request):
        mapping = request.query_params.get('mapping')

        filters = Q()
        if mapping:
            filters &= Q(subject_mapping_id=mapping)

        subject_component = Component.objects.filter(filters).distinct().order_by('-id')

        return Response({
            "message": "Subject mappings fetched successfully",
            "data": ComponentMixSerializer(subject_component, many=True).data
        })
    

from django.utils.timezone import now
def get_current_batches():
    """Fetch batches that are currently active based on today's date."""
    today = now().date()
    return Batch.objects.filter(start_date__lte=today, end_date__gte=today, is_active=True)

def get_current_terms():
    """Fetch terms associated with currently active batches."""
    current_batches = get_current_batches()
    return Terms.objects.filter(subject_mappings__batch__in=current_batches).distinct()


class FAcultyFilterAPIView(APIView):
    def get(self, request):
        faculty = request.query_params.get('faculty')
        # current_terms = get_current_terms()
        # import pdb; pdb.set_trace()
        filters = Q()
        if faculty:
            filters &= Q(faculty_id=faculty)
        # if current_terms:
        #     filters &= Q(term__in=current_terms)
        
        subject_assign = SubjectMapping.objects.filter(filters).distinct().order_by('-id')

        return Response({
            "message": "Subject mappings fetched successfully",
            "data": FacultyMixSerializer(subject_assign, many=True).data
        })
    


class EmployeeSingleListAPIView(APIView):
    def get(self, request):
        employee = Employee.objects.filter(employee_type = 'Teaching').order_by('-id')
        return Response({"message": "Employee fetched successfully", "data": EmployeeMixSerializer(employee, many=True).data})




class StudentSingleListAPIView(APIView):
    def get(self, request):
        course = request.query_params.get('course')
        batch = request.query_params.get('batch')
        filters = Q()
        if course:
            filters &= Q(course__id=course)
        if batch:
            filters &= Q(batch_id=batch)
        student = Student.objects.filter(filters).order_by('-id')
        return Response({"message": "Student fetched successfully", "data": StudentMixSerializer(student, many=True).data})


class MembershipFilterAPIView(APIView):
    def get(self, request):
        course = request.query_params.get('course')
        batch = request.query_params.get('batch')

        filters = Q()
        if course:
            filters &= Q(course__id=course)
        if batch:
            filters &= Q(batch_id=batch)
        students = Student.objects.filter(filters).distinct().order_by('-id')
        mentored_student_ids = FacultyMentorship.objects.filter(students__in=students).values_list('students__id', flat=True)
        students =  students.exclude(id__in=mentored_student_ids)
        students =  StudentMixSerializer(students , many= True)
        return response_handler(message="student list fetched successfully"  , code = 200 , data=students.data)
    

class ScheduleClassFacultyWise(APIView):
    def get(self, request , faculty_id):
        today = datetime.today().date()
        schedule_class = ClassSchedule.objects.filter(mapping__faculty = faculty_id , is_complete = False , date__gte = today).order_by('-id')
        schedule_class= ClassScheduledListSerializer(schedule_class , many = True)
        return response_handler(message="Scheduled class fetched successfully" , code = 200   ,  data=schedule_class.data)
    

class ComponentSubjectWise(APIView):
    def get(self, request , subject_id):
        component = Component.objects.filter(subject_mapping = subject_id).order_by('-id')
        component= ComponentMixListSerializer(component , many = True)
        return response_handler(message="Component fetched successfully" , code = 200   ,  data=component.data)

class SubComponentComponentWise(APIView):
    def get(self, request , component_id):
        sub_component = SubComponent.objects.filter(component = component_id).order_by('-id')
        sub_component= SubComponentMixListSerializer(sub_component , many = True)
        return response_handler(message="Component fetched successfully" , code = 200   ,  data=sub_component.data)
    
class ScheduleclassSubjectWise(APIView):
    def get(self, request , subject_id):
        schedule_class = ClassSchedule.objects.filter(mapping = subject_id).order_by('-id')
        schedule_class= ClassScheduledListSerializer(schedule_class , many = True)
        return response_handler(message="Schedule class fetched successfully" , code = 200   ,  data=schedule_class.data)
    

class SubjectStudentWise(APIView):
    def get(self, request , student_id):
        student = get_object_or_404(Student , id = student_id)
        student_mapping = StudentMapping.objects.filter(student = student)
        subject_mapping = SubjectMapping.objects.filter(
            batch = student.batch,
            course = student.course,
            term__in = student_mapping.values_list('term' , flat=True),
            specialization__in = student_mapping.values_list('specialization' , flat=True))
        subject_mapping = SubjectMappingListSerializer(subject_mapping , many = True)
        return response_handler(message="subject list fetyched successfully" , code = 200 , data=subject_mapping.data)
    

class DashBoardCountAPIView(APIView):
    def get(self, request):
        student = Student.objects.filter(user__is_active = True , is_archived = False , dropped = False , passout_status = False).count()
        course = Course.objects.filter(is_active  = True).count()
        subject = Subject.objects.filter(is_active = True).count()
        faculty = Employee.objects.filter(is_archived = False , user__is_active = True , employee_type = "Teaching").count()
        response_data = {
            "student_count":student,
            "course_count":course,
            "subject_count":subject,
            "faculty_count": faculty

        }
        return response_handler(message='count list ' , code = 200 , data=response_data)
    


class ExamSubjectWiseAPIView(APIView):
    def get(self, request , subject_id):
        exam  = Exam.objects.filter(component__subject_mapping = subject_id)
        exam = ExamListSerializer(exam , many = True)
        return response_handler(message = "exam list fetched successfully" , code = 200 , data =exam.data)
    

class DashBoardStudentDataAPIView(APIView):
    def get(self, request, student_id):
        student = get_object_or_404(Student , id = student_id)
        student = DashBoardStudentDataSerializer(student)
        # import pdb; pdb.set_trace()
        return response_handler(message = "student data detched successfully" , code = 200 , data=student.data)
    


class EmployeeSummary(APIView):
    def get(self, request , faculty_id):
        today = datetime.today().date()
        data = {}
        employee  =  get_object_or_404(Employee , id = faculty_id)
        employee =  EmployeeListSerializer(employee)
        schedule_class = ClassSchedule.objects.filter(mapping__faculty = faculty_id , is_complete = False , date__gte = today).order_by('-id')
        schedule_class= ClassScheduledListSerializer(schedule_class , many = True)
        subject_assign = SubjectMapping.objects.filter(faculty_id=faculty_id).distinct().order_by('-id')
        subject_assign= FacultyMixSerializer(subject_assign , many = True)
        data['employee'] = employee.data
        data['schedule_class'] = schedule_class.data
        data['subject_assign'] = subject_assign.data

        return response_handler(message="employee data fetched successfully" , code = 200 , data  =data)
    


class StudentBatchwise(APIView):
    def get(self, request , batch):
        student = Student.objects.filter(batch = batch)
        student = StudentMixSerializer(student ,many = True)
        return response_handler(message="student list fetched successfully" , code = 200 , data = student.data)