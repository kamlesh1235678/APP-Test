from rest_framework import serializers 
from django.contrib.auth.models import *
from modules.privacy.models import *


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = "__all__"