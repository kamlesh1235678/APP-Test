from rest_framework import serializers
from modules.administration.models import *

class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = "__all__"


# class BatchTermCourseMappingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BatchTermCourseMapping
#         fields = "__all__"