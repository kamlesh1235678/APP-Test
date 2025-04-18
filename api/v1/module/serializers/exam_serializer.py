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


class ExamSubjectMappingSerializer(serializers.ModelSerializer):
    subject = SubjectMixSerializer()
    component = serializers.SerializerMethodField()

    class Meta:
        model = SubjectMapping
        fields = ['subject', 'component']

    def get_component(self, obj):
        component = Component.objects.filter(subject_mapping=obj, name="Final").first()
        if component:
            return {
                "id": component.id,
                "name": component.name,
            }
        return None
    

class HallTicketAnnounceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HallTicketAnnounce
        fields = "__all__"