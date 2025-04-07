from rest_framework import serializers
from modules.administration.models import *

class InternshipCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipCompany
        fields = "__all__"

class InternshipReportSerializer(serializers.ModelSerializer):
    main_report = serializers.FileField(required=False)
    weekly_report = serializers.ListField(child=serializers.CharField(), read_only=True)  # Read-only list of file paths

    class Meta:
        model = InternshipReport
        fields = ["id", "internship_company", "main_report", "weekly_report"]