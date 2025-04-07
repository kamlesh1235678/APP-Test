from rest_framework import serializers 
from modules.administration.models import *


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"