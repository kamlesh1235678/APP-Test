from rest_framework import serializers
from modules.administration.models import *

class EventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = "__all__"