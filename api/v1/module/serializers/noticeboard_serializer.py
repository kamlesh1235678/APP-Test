from rest_framework import serializers
from modules.administration.models import NoticeBoard


class NoticeBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeBoard
        fields = "__all__"
