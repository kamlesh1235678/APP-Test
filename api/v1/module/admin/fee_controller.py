# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from modules.users.models import StudentFeeStatus, Student
from modules.administration.models import ResetExamRequest
from api.v1.module.serializers.fee_serializer import StudentFeeStatusSerializer
from api.v1.module.response_handler import *
from django.shortcuts import get_object_or_404
from django.db.models import Q

class StudentFeeStatusAPIView(APIView):
    def get(self, request):
        batch = request.query_params.get('batch')
        course = request.query_params.get('course')
        enrollment_number = request.query_params.get('enrollment_number')

        filters = Q()
        if batch:
            filters &= Q(batch_id=batch)
        if course:
            filters &= Q(course_id=course)
        if enrollment_number:
            filters &= Q(enrollment_number=enrollment_number)

        student = Student.objects.filter(filters).select_related('batch', 'course').first()

        if not student:
            return response_handler(message="Student not found", code=404, data={})

        try:
            fee_status = StudentFeeStatus.objects.get(student=student)
            fee_data = {
                "student_id": student.id,
                "name": f"{student.first_name} {student.middle_name} {student.last_name}",
                "email": student.user.email,
                "mobile": student.contact_number,
                "enrollment_number": student.enrollment_number,
                "batch": student.batch.name,
                "course": student.course.name,
                "form_fee": fee_status.form_fee,
                "program_fee_paid": fee_status.program_fee_paid,
                "enrollment_fee_paid": fee_status.enrollment_fee_paid,
                "caution_fee_tuition": fee_status.caution_fee_tuition,
                "extra_penalty": fee_status.extra_penalty,
            }
        except StudentFeeStatus.DoesNotExist:
            fee_data = {
                "student_id": student.id,
                "name": f"{student.first_name} {student.middle_name} {student.last_name}",
                "email": student.user.email,
                "mobile": student.contact_number,
                "enrollment_number": student.enrollment_number,
                "batch": student.batch.name,
                "course": student.course.name,
                "form_fee": True,
                "program_fee_paid": True,
                "enrollment_fee_paid": True,
                "caution_fee_tuition": True,
                "extra_penalty": True,
            }

        # Check for resit exams and include subject-wise fee statuses if applicable
        resits = ResetExamRequest.objects.filter(student=student).select_related('subjects')
        if resits.exists():
            fee_data["resit_subjects"] = [
                {
                    "subject": resit.subjects.subject.name,
                    "resit_fee_paid": resit.status,
                    "resit_id": resit.id
                }
                for resit in resits
            ]
        else:
            fee_data["resit_subjects"] = []

        return response_handler(message="Student fee statuses fetched successfully", code=200, data=fee_data)



    def post(self, request):
        data = request.data
        enrollment_number = data.get("enrollment_number")
        if not enrollment_number:
            return response_handler(message="Enrollment number is required", code=400, data={})
        try:
            student = Student.objects.get(enrollment_number=enrollment_number)
        except Student.DoesNotExist:
            return response_handler(message="Student not found", code=404, data={})

        # Create or update main fee status
        fee_status, created = StudentFeeStatus.objects.get_or_create(student=student)
        fee_status.form_fee = data.get("form_fee", fee_status.form_fee)
        fee_status.program_fee_paid = data.get("program_fee_paid", fee_status.program_fee_paid)
        fee_status.enrollment_fee_paid = data.get("enrollment_fee_paid", fee_status.enrollment_fee_paid)
        fee_status.caution_fee_tuition = data.get("caution_fee_tuition", fee_status.caution_fee_tuition)
        fee_status.extra_penalty = data.get("extra_penalty", fee_status.extra_penalty)
        fee_status.save()

        # Handle resit subjects if provided
        resit_updates = data.get("resit_subjects", [])
        for item in resit_updates:
            resit_id = item.get("resit_id")
            fee_paid = item.get("resit_fee_paid")
            if resit_id is not None:
                try:
                    resit = ResetExamRequest.objects.get(pk = resit_id)
                    resit.status = fee_paid
                    resit.save()
                except ResetExamRequest.DoesNotExist:
                    continue  # You can also choose to create it if needed
        return response_handler(message="Student fee and resit status updated" if not created else "Student fee and resit status created",
            code=200 , data={})
