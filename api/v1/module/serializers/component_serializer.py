from rest_framework import serializers
from modules.administration.models import *

class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = "__all__"

class SubComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SubComponent
        fields = "__all__"



class ComponentAnswersSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ComponentAnswers
        fields = "__all__"

class SubComponentAnswersSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SubComponentAnswers
        fields = "__all__"