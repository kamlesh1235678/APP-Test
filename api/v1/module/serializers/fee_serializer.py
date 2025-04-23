# serializers.py
from rest_framework import serializers
from modules.users.models import StudentFeeStatus

class StudentFeeStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentFeeStatus
        fields = '__all__'
