from rest_framework import serializers
from api.v1.module.serializers.student_serializer import UserSerializer
from modules.users.models import User , AuditLog  
from django.contrib.auth.models import Permission
from modules.privacy.models import RolePermission
import hashlib
import pandas as pd


def save_hashed_permissions_to_excel(hashed_map, filename='permission_hashes.xlsx'):
    df = pd.DataFrame([
        {"Hashed Code": key, "Codename": value}
        for key, value in hashed_map.items()
    ])
    df.to_excel(filename, index=False)

class LoginSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()
    role_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    employee_type = serializers.SerializerMethodField()
    user_id  = serializers.SerializerMethodField()
    permission_list = serializers.SerializerMethodField()
    

    class Meta:
        model = User
        exclude = ['password', 'is_staff', 'is_superuser', 'is_active', 'is_lock', 'last_login']

    def get_role_name(self, obj):
        """Get role name dynamically from related Student or Employee"""
        if hasattr(obj, 'student'):
            return obj.student.student_role.name
        elif hasattr(obj, 'employee'):
            return [role.name for role in obj.employee.employee_role.all()]
        return None
    
    def get_user_id(self, obj):
        """Get role name dynamically from related Student or Employee"""
        if hasattr(obj, 'student'):
            return obj.student.id
        elif hasattr(obj, 'employee'):
            return obj.employee.id
        return None

    def get_role_id(self, obj):
        """Get role ID dynamically from related Student or Employee"""
        if hasattr(obj, 'student'):
            return obj.student.student_role.id
        elif hasattr(obj, 'employee'):
            return [role.id for role in obj.employee.employee_role.all()]
        return None
    
    def get_employee_type(self, obj):
        """Get role ID dynamically from related Student or Employee"""
        if hasattr(obj, 'student'):
            return None
        elif hasattr(obj, 'employee'):
            return obj.employee.employee_type
        return None
    
    def get_name(self, obj):
        if hasattr(obj, 'student'):
            return f"{obj.student.first_name} {obj.student.last_name}"
        elif hasattr(obj, 'employee'):
            return f"{obj.employee.first_name} {obj.employee.last_name}"
        return None
    
    def get_permission_list(self, obj):
        permissions = []

        if hasattr(obj, 'student'):
            role = obj.student.student_role
            if role:
                role_permissions = role.role_permissions.all().first()
                if role_permissions:
                    permissions = role_permissions.permission.all().values_list('codename', flat=True)

        elif hasattr(obj, 'employee'):
            roles = obj.employee.employee_role.all()
            permissions = Permission.objects.filter(
                role_permissions__role__in=roles
            ).values_list('codename', flat=True).distinct()

        # Hash permissions
        hashed_map = { 
            hashlib.sha256(code.encode()).hexdigest(): code   # codename hashed in sha256 with 16 digit
            for code in permissions
        }
        hashed_list = list(hashed_map.keys())
        return hashed_list


    

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = "__all__"

    def get_user(self, obj):
        # Assuming `user` is a related field on the AuditLog model
        if obj.user:
            return obj.user.email
        return None