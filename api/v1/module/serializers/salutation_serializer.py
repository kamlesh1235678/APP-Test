from rest_framework import serializers 
from modules.administration.models import *


class SalutationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salutation
        fields = "__all__"