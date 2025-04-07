from rest_framework import serializers 
from modules.administration.models import *


class StudentLeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentLeaveRequest
        fields = "__all__"