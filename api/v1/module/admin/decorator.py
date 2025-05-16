
from functools import wraps
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from modules.administration.models import ClassSchedule , ResetExamRequest
from modules.users.models import StudentFeeStatus , Student
from api.v1.module.response_handler import *
from rest_framework import status as http_status



def validate_attendance_time(func):
    @wraps(func)
    
    def wrapper(instance, *args, **kwargs):
        class_id = kwargs['class_id']
        class_schedule = get_object_or_404(ClassSchedule , id = class_id)
        current_time = now()
        if class_schedule.date >= current_time.date():
            return response_handler(message = "Attendance cannot be marked before the class date." , code = 400 ,data= {})
            
        if class_schedule.date == current_time.date() and class_schedule.end_time > current_time.time():
            return response_handler(message = "Attendance cannot be marked before the class date." , code = 400 ,data= {})

        return func(instance, *args, **kwargs)
    return wrapper




def check_fee_status(view_func):
    @wraps(view_func)
    def _wrapped_view(self, request, student_id, term_id, type, *args, **kwargs):
        student = get_object_or_404(Student, id=student_id)
        if type != "main":
            fee_status = StudentFeeStatus.objects.filter(student=student).first()
            if not fee_status or not fee_status.program_fee_paid:
                return response_handler(message = "Program fee not paid. Please pay to download hall ticket" , code = 400 ,data= {})
        elif type in ["resit-1", "resit-2"]:
            resits = ResetExamRequest.objects.filter(student=student, term_id=term_id, type=type, status=True)
            if not resits.exists():
                return response_handler(message = f"{type.replace('-', ' ').capitalize()} fee not paid or request not approved." , code = 400 ,data= {})
        return view_func(self, request, student_id, term_id, type, *args, **kwargs)
    return _wrapped_view
