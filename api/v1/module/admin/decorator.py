
from functools import wraps
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from modules.administration.models import ClassSchedule
from api.v1.module.response_handler import *



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
