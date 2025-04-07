from rest_framework import serializers
from modules.administration.models import *
from modules.users.models import *

class TermsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terms
        fields = "__all__"









