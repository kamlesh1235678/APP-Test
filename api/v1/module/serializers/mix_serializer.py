from rest_framework import serializers
from modules.administration.models import *
from modules.users.models import *
from api.v1.module.serializers.student_serializer import *
from django.utils.timezone import now
from datetime import datetime


class SpecializationMixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id' , 'name']

class BatchMixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['id' , 'name']

class TermsMixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terms
        fields = ['id' , 'name']

class CourseMixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id' , 'name']

class SubjectMixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id' , 'name']

class EmployeeMixSerializer(serializers.ModelSerializer):
    user = UserListSerializer()
    class Meta:
        model = Employee
        fields = ['id' , 'first_name' , 'last_name', 'user' , 'salutation']

class SubjectMappingMixSerializer(serializers.ModelSerializer):
    subject = SubjectMixSerializer()
    class Meta:
        model = SubjectMapping
        fields = ['id' , 'subject',]


class ComponentMixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = ['id' , 'name' , 'type' ]


class FacultyMixSerializer(serializers.ModelSerializer):
    term = TermsMixSerializer()
    batch = BatchMixSerializer()
    course = CourseMixSerializer(many=True)
    specialization = SpecializationMixSerializer(many=True)
    subject = SubjectMixSerializer()
    faculty= EmployeeMixSerializer()
    class Meta:
        model = SubjectMapping
        fields = "__all__"

class StudentMixSerializer(serializers.ModelSerializer):
    batch = BatchMixSerializer()
    course = CourseMixSerializer()
    user = UserSerializer()
    class Meta:
        model = Student
        fields = ['id', 'first_name','middle_name', 'last_name' , 'contact_number', 'gender' ,'enrollment_number' , 'user' , 'batch' , 'course']



class ComponentMixListSerializer(serializers.ModelSerializer):
    is_answer_add_status = serializers.SerializerMethodField()
    is_marks_add_status = serializers.SerializerMethodField()
    class Meta:
        model = Component
        fields = "__all__"

    def get_is_answer_add_status(self, obj):
        current_time = now()
        if obj.start_date and obj.end_date:
            return obj.start_date <= current_time <= obj.end_date
        return False  # Default to False if dates are missing

    def get_is_marks_add_status(self, obj):
        if obj.is_submission:
            current_time = now()
            if obj.start_date:
                return current_time > obj.start_date
            return False
        return True



class SubComponentMixListSerializer(serializers.ModelSerializer):
    is_answer_add_status = serializers.SerializerMethodField()
    is_marks_add_status = serializers.SerializerMethodField()
    class Meta:
        model  = SubComponent
        fields = "__all__"

    def get_is_answer_add_status(self, obj):
        current_time = now()
        if obj.start_date and obj.end_date:
            return obj.start_date <= current_time <= obj.end_date
        return False  # Default to False if dates are missing

    def get_is_marks_add_status(self, obj):
        if obj.is_submission:
            current_time = now()
            if obj.start_date:
                return current_time > obj.start_date
            return False
        return True
        
class DashBoardStudentDataSerializer(serializers.ModelSerializer):
    batch = BatchMixSerializer()
    course = CourseMixSerializer()
    user = UserSerializer()
    upcoming_class = serializers.SerializerMethodField()
    mentor_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'middle_name', 'last_name', 'contact_number', 
            'gender', 'enrollment_number', 'user', 'batch', 'course', 
            'upcoming_class', 'mentor_name'
        ]

    def get_upcoming_class(self, obj):
        # Directly use the fields from `obj` rather than querying again
        student = obj
        student_mappings = StudentMapping.objects.filter(student=student)
        
        # Get the subject mappings based on student batch, course, term, and specialization
        subject_mappings = SubjectMapping.objects.filter(
            batch=student.batch,
            course=student.course,
            term__in=student_mappings.values_list("term", flat=True),
            specialization__in=student_mappings.values_list("specialization", flat=True)
        )
        
        # Get today's date and count upcoming classes
        today = datetime.today().date()
        upcoming_classes_count = ClassSchedule.objects.filter(
            mapping__in=subject_mappings,
            is_complete=False,  # Ensures that completed classes are not counted
            date__gte=today      # Ensures that only future classes are counted
        ).count()

        return upcoming_classes_count

    def get_mentor_name(self, obj):
        # Directly use the student `obj` for the relationship
        student = obj
        faculty = FacultyMentorship.objects.filter(students=student).first()
        
        if faculty:
            # Construct the faculty name using their salutation and name
            faculty_name = f"{faculty.user.salutation} {faculty.user.first_name} {faculty.user.last_name}"
            return faculty_name
        return None  # If no mentor is found, return None or an appropriate fallback




class StudentMappingFiterSerializer(serializers.ModelSerializer):
    batch = BatchMixSerializer()
    course = CourseMixSerializer()
    specialization = SpecializationMixSerializer()
    term = TermsMixSerializer()
    class Meta:
        model = StudentMapping
        fields = "__all__"



class StudentMixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'first_name','middle_name', 'last_name' , 'enrollment_number' ]

