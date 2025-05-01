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

class ResetExamRequestListtSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    term = serializers.SerializerMethodField()
    subjects = serializers.SerializerMethodField()
    class Meta:
        model = ResetExamRequest
        fields =  ['student' , 'type' , 'batch' ,'course' , 'term' , 'subjects' , 'status']

    def get_student(self, obj):
        if obj.student:
            return f"{obj.student.first_name} {obj.student.middle_name} {obj.student.last_name}"
    def get_batch(self, obj):
        if obj.batch:
            return obj.batch.name
    def get_term(self, obj):
        if obj.term:
            return obj.term.name
    def get_course(self, obj):
        if obj.course:
            return obj.course.name
    def get_subjects(self, obj):
        if obj.subjects:
            return obj.subjects.subject.name