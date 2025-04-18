from rest_framework import serializers
from modules.users.models import *

class AdmitCardStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "full_name", "roll_no", "email", "phone"]
