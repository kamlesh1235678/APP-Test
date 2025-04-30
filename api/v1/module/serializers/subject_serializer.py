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


class SubjectMappingNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectMappingNotes
        fields = "__all__"

class SubjectMappingNotesListSerializer(serializers.ModelSerializer):
    mapping = SubjectMappingListSerializer()
    class Meta:
        model = SubjectMappingNotes
        fields = "__all__"


class FinalSubjectResultSerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()
    subject_code = serializers.SerializerMethodField()
    credit = serializers.SerializerMethodField()
    total_marks = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    external_marks = serializers.SerializerMethodField()
    internal_marks = serializers.SerializerMethodField()
    grade_point = serializers.SerializerMethodField()
    get_credit_xgp = serializers.SerializerMethodField()
    is_pass = serializers.SerializerMethodField()
    class Meta:
        model = FinalSubjectResult
        fields = ['subject_name', 'subject_code', 'credit', 'total_marks' ,'grade' 'is_pass' ,'get_credit_xgp' , 'grade_point' ,'internal_marks' , 'external_marks' ]

    def get_subject_name(self, obj):
        if obj.subject_mapping:
            return obj.subject_mapping.subject.name
    def get_subject_code(self, obj):
        if obj.subject_mapping:
            return obj.subject_mapping.subject.code
    def get_credit(self, obj):
        if obj.subject_mapping:
            return obj.subject_mapping.subject.credit
    def get_total_marks(self, obj):
        if obj.total_marks:
            return obj.total_marks
    def get_external_marks(self, obj):
        if obj.external_marks:
            return obj.external_marks
    def get_internal_marks(self, obj):
        if obj.internal_marks:
            return obj.internal_marks
    def get_grade_point(self, obj):
        if obj.grade_point:
            return obj.grade_point
    def get_grade(self, obj):
        if obj.grade:
            return obj.grade
    def get_get_credit_xgp(self, obj):
        if obj.get_credit_xgp:
            return obj.get_credit_xgp
    def get_is_pass(self, obj):
        if obj.is_pass:
            return obj.is_pass

