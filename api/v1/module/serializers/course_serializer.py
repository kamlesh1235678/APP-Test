from rest_framework import serializers
from modules.administration.models import *

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"