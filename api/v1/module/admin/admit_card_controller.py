from modules.administration.models import *
from api.v1.module.serializers.batch_serializer import *
from api.v1.module.response_handler import *
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from api.v1.module.serializers.admit_card_serializer import AdmitCardStudentSerializer

class AdmitCardView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        term_id = request.query_params.get("term_id")
        student_id = request.query_params.get("student_id")

        if not term_id:
            return response_handler(message="term_id is required", code=400, data={})
        if not student_id:
            return response_handler(message="student_id is required", code=400, data={})

        student = get_object_or_404(Student, id=student_id)
        batch = student.batch
        course = student.course

        # Filter all mappings where this student is part of the ManyToMany and term matches
        mappings = StudentMapping.objects.filter(
            term_id=term_id,
            student=student
        )

        if not mappings.exists():
            return response_handler(message="No mapping found for this student and term", code=404, data={})

        # Get all specialization names from matching mappings
        specialization_names = [mapping.specialization.name for mapping in mappings]

        data = {
            "student_enrollment_number": student.enrollment_number,
            "student_aicte_permanent_id": student.aicte_permanent_id,
            "student_name": f"{student.first_name}{student.middle_name}{student.last_name}",
            "batch": batch.name if batch else None,
            "course": course.name if course else None,
            "term_id": get_object_or_404(Terms , id = term_id).name,
            "specializations": specialization_names,
        }

        return response_handler(message="Admit card data fetched successfully", code=200, data=data)



class HallTicketWise(APIView):
    def get(self, request , student_id , term_id):
        student = get_object_or_404(Student , id = student_id)
        term =  get_object_or_404(Terms , id = term_id)
        student_mapping = StudentMapping.objects.filter(student = student)
        subject_mapping = SubjectMapping.objects.filter(
            batch = student.batch,
            course = student.course,
            term__in = student_mapping.values_list('term' , flat=True),
            specialization__in = student_mapping.values_list('specialization' , flat=True))
        subject_data = []
        for subject in subject_mapping:
            exam = Exam.objects.filter(component__subject_mapping = subject).first()
            subject_data.append({
                        "subject_name": subject.subject.name if subject.subject and subject.subject.name else None,
                        "exam_date": exam.date if exam and exam.date else None,
                        "start_time": exam.start_time if exam and exam.start_time else None,
                        "duration": exam.duration if exam and exam.duration else None,
                        })
        hall_ticket =  {"student_name": f"{student.first_name}{student.middle_name}{student.last_name}" ,
                        "student_batch" : student.batch.name,
                        "student_course": student.course.name,
                        "student_father_name": student.father_name , 
                        "student_enrollment_number": student.enrollment_number ,
                        "student_specialization":student_mapping.values_list('specialization__name' , flat=True) , 
                        "student_term": term.name , 
                        "subject_data": subject_data}
        return response_handler(message="subject list fetyched successfully" , code = 200 , data=hall_ticket)
    