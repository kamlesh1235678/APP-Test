from rest_framework import serializers
from modules.users.models import *
from api.v1.module.serializers.student_serializer import *
from api.v1.module.serializers.employee_serializer import *

class StudentProfileSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    class Meta:
        model = User
        fields = ['student']

class EmployeeProfileSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer()
    class Meta:
        model = User
        fields = ['employee']