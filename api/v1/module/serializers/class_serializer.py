from rest_framework import serializers 
from modules.administration.models import *
from api.v1.module.serializers.subject_serializer import *
from django.utils.timezone import now

class ClassScheduledSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSchedule
        fields = "__all__"

class ClassScheduledListSerializer(serializers.ModelSerializer):
    mapping = SubjectMappingListSerializer()
    is_ready_for_attendance = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassSchedule
        fields = "__all__"

    def get_is_ready_for_attendance(self, obj):
        current_time = now()
        # import pdb; pdb.set_trace()
        return obj.date <= current_time.date() or (obj.date == current_time.date() and obj.start_time <= current_time.time())
    


    