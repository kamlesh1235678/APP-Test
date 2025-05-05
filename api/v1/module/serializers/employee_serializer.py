# serializers.py
from rest_framework import serializers
from modules.users.models import  *
from api.v1.module.serializers.student_serializer import *
from api.v1.module.serializers.department_serializer import *
from api.v1.module.serializers.designation_serializer import *
from api.v1.module.serializers.salutation_serializer import *
from api.v1.module.serializers.role_serializer import *
from api.v1.module.serializers.mix_serializer import *




class EmployeeSerializer(serializers.ModelSerializer):
    user =  UserSerializer(required = False)

    class Meta:
        model = Employee
        fields = "__all__"

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        employee_roles_data = validated_data.pop('employee_role', [])
        user_serializer = UserSerializer(data = user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        employee = Employee.objects.create(user = user , **validated_data)
        employee.employee_role.set(employee_roles_data)
        return employee


class EmployeeListSerializer(serializers.ModelSerializer):
    user = UserListSerializer()
    institute_department = DepartmentSerializer()
    employee_role = RoleSerializer(many=True)
    designation = DesignationSerializer()
    salutation = SalutationSerializer()

    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeArchivedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['is_archived']




class FacultyMentorshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacultyMentorship
        fields = "__all__"


class FacultyMentorshipListSerializer(serializers.ModelSerializer):
    students = StudentMixSerializer(many = True)
    user = EmployeeMixSerializer()
    class Meta:
        model = FacultyMentorship
        fields = "__all__"


class RoleAssignmentSerializer(serializers.ModelSerializer):
    assigned = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'name', 'assigned']

    def get_assigned(self, role):
        employee = self.context.get('employee')
        if employee:
            return role in employee.employee_role.all()
        return False
    
class RoleUpdateSerializer(serializers.Serializer):
    role_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True
    )