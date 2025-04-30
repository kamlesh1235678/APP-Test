from rest_framework import serializers
from modules.administration.models import *
from api.v1.module.serializers.mix_serializer import StudentMixSerializer


class ResetExamRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResetExamRequest
        fields =  "__all__"

class ResetExamRequestListSerializer(serializers.ModelSerializer):
    student = StudentMixSerializer()
    class Meta:
        model = ResetExamRequest
        fields =  ['student' , 'criteria_first' , 'criteria_second']