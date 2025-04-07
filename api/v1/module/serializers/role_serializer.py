from rest_framework import serializers 
from modules.administration.models import *


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"