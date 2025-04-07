from rest_framework import serializers
from modules.administration.models import *
from api.v1.module.serializers.mix_serializer import *

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = "__all__"

class ExamListSerializer(serializers.ModelSerializer):
    component = ComponentMixListSerializer()
    class Meta:
        model = Exam
        fields = "__all__"

class ExamActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['is_active']

class ExamCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['is_cancel']


