from rest_framework import serializers
from modules.administration.models import *


class ResetExamRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResetExamRequest
        fields =  "__all__"