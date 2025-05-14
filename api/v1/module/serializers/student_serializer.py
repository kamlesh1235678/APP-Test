# serializers.py
from rest_framework import serializers
from modules.users.models import *
from api.v1.module.serializers.student_serializer import *
from api.v1.module.serializers.batch_serializer import *
from api.v1.module.serializers.course_serializer import *
from api.v1.module.serializers.role_serializer import *
from django.utils.crypto import get_random_string

class UserSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'user_type']

    # def __init__(self, *args ,**kwargs):
    #     super().__init__(*args, **kwargs)
    #     require_password = self.context.get('require_password' ,True )
    #     if not require_password:
    #         self.fields['password'].required  = False

    def create(self, validated_data):
        # password = get_random_string(length=12)
        password = "taxila@123"
        user = User.objects.create(**validated_data)
        user.set_password(password)  # Hash the password
        user.save()
        return user
    
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'user_type' ,'is_active']

    
class StudentListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    batch = BatchSerializer()
    course = CourseSerializer()
    student_role = RoleSerializer()

    class Meta:
        model = Student
        fields = "__all__"
    
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password' , 'is_staff' , 'is_superuser'  , 'user_type' , 'last_login' , 'id']
        
class UserLockSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_lock']
        
class UserActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_active']


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(required = False)  # Nested User serializer

    class Meta:
        model = Student
        fields ="__all__"

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        student = Student.objects.create(user=user, **validated_data)
        return student
    
    # def update(self, instance, validated_data):
    #     user_data = validated_data.pop('user', None)
    #     if user_data:
    #         user_instance = instance.user  # Get the related User instance
    #         user_serializer = UserSerializer(user_instance, data=user_data, partial=True)
    #         user_serializer.is_valid(raise_exception=True)
    #         user_serializer.save()

    #     # Update the student instance fields dynamically
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     instance.save()
        
    #     return instance


class StudentArchivedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['is_archived']

#student mapping serializers
class StudentMappingSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Student.objects.filter(is_archived = False)
    )
    class Meta:
        model = StudentMapping
        fields = "__all__"

class StudentMappingListSerializer(serializers.ModelSerializer):
    student = StudentSerializer(many=True, read_only=True)
    class Meta:
        model = StudentMapping
        fields = "__all__"

class StudentMappingLListSerializer(serializers.ModelSerializer):
    term = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    specialization = serializers.SerializerMethodField()

    class Meta:
        model = StudentMapping
        fields = ["id", "batch", "term", "course", "specialization"]

    def get_batch(self, obj):
        return obj.batch.name if obj and obj.batch else None

    def get_course(self, obj):
        return obj.course.name if obj and obj.course else None

    def get_term(self, obj):
        return obj.term.name if obj and obj.term else None

    def get_specialization(self, obj):
        return obj.specialization.name if obj and obj.specialization else None

class StudentSpecilaizationSerializer(serializers.ModelSerializer):
    is_exist = serializers.SerializerMethodField() 

    class Meta:
        model = StudentMapping
        fields = ["id", "batch", "term", 'student', "course", "specialization", "is_exist"]

    def get_is_exist(self, obj):
        student = self.context.get('student')  
        if student:
            return student in obj.student.all()  
        return False
    

class StudentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        fields = "__all__"


