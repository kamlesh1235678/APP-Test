from rest_framework import serializers 
from django.contrib.auth.models import *
from modules.privacy.models import *


class PermissionSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    class Meta:
        model = Permission
        fields = "__all__"
        
    def get_content_type(self, obj):
        if obj.content_type:
            return obj.content_type.model
        else:
            return None

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = "__all__"