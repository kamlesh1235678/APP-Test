from rest_framework import serializers 
from modules.administration.models import *


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = "__all__"