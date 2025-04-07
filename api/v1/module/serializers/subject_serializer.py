from rest_framework import serializers
from modules.administration.models import *
from api.v1.module.serializers.mix_serializer import *

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class SubjectMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectMapping
        fields = "__all__"

    def validate(self, data):
        if data["weightage_external"] + data["weightage_internal"] != 100:
            raise serializers.ValidationError(
                "The sum of Weightage External and Internal must be 100%."
            )
        return data
    
class BulkSubjectMappingSerializer(serializers.ModelSerializer):
    subjects = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all()),
        write_only=True
    )

    class Meta:
        model = SubjectMapping
        fields = '__all__'

    def create(self, validated_data):
        """Create multiple SubjectMapping instances."""
        subjects = validated_data.pop("subjects", [])
        created_mappings = []

        for subject in subjects:
            mapping = SubjectMapping.objects.create(subject=subject, **validated_data)
            created_mappings.append(mapping)

        return created_mappings



class SubjectMappingListSerializer(serializers.ModelSerializer):
    term = TermsMixSerializer()
    batch = BatchMixSerializer()
    course = CourseMixSerializer(many=True)
    specialization = SpecializationMixSerializer(many=True)
    subject = SubjectMixSerializer()
    faculty= EmployeeMixSerializer()
    class Meta:
        model = SubjectMapping
        fields = "__all__"


class SubjectMappingSyllabusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectMappingSyllabus
        fields = "__all__"

class SubjectMappingSyllabusListSerializer(serializers.ModelSerializer):
    mapping = SubjectMappingListSerializer()
    class Meta:
        model = SubjectMappingSyllabus
        fields = "__all__"



