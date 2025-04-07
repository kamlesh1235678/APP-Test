from rest_framework import serializers 
from modules.administration.models import *


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = "__all__"