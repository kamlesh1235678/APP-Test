import os
from rest_framework import viewsets
from modules.administration.models import *
from modules.users.models import *
from api.v1.module.serializers.intership_serializer import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from api.v1.module.response_handler import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from api.v1.module.serializers.student_serializer import *
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError , NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status


class InternshipCompanyPagination(PageNumberPagination):
    page_size = 10
    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        if not total_items:
            return Response({'message':'Internship Company no found' , 'code':400 , 'data':[] , 'extra':{}})
        if self.page_size:
            total_page = math.ceil(total_items/self.page_size)
        message = "Internship Company List fetch successfully"
        return Response({'message':message , 'code': 200 , 'data':data})

class InternshipCompanyModelViewSet(viewsets.ModelViewSet):
    queryset = InternshipCompany.objects.all().order_by('-id')
    serializer_class = InternshipCompanySerializer
    pagination_class = InternshipCompanyPagination
    http_method_names = ['get' , 'post' , 'put' , 'delete']
    filter_backends =[SearchFilter , DjangoFilterBackend]


    def get_queryset(self):
        try:
            return super().get_queryset()
        except:
            message = "Internship Company no found"
            return response_handler(message= message , code = 400 , data={})
        
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request , *args , **kwargs)
            message = "Internship Company create successfully"
            return response_handler(message=message , code = 200  , data =  response.data)
        except ValidationError as e:
            return response_handler( message=format_serializer_errors(e.detail), code=400,data={})
        except Exception as e:
            if isinstance(e.args[0], dict):  
                formatted_errors = format_serializer_errors(e.args[0])
                return response_handler(message=formatted_errors[0], code=400, data={})
            else:
                return response_handler(message=str(e), code=400, data={})
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer =  self.serializer_class(instance , data = request.data , partial = True)
        if serializer.is_valid():
            serializer.save()
            message = "Internship Company Updated successfully"
            return response_handler(message = message , code = 200 , data = serializer.data)
        message = "Something went wrong"
        return response_handler(message=message , code = 400 , data = {})
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            response = self.get_serializer(instance)
            message = "Internship Company data retrived successfully"
            return response_handler(message = message , code = 200 , data = response.data)
        except NotFound:
            return response_handler(message="InternshipCompany No found" , code = 400 , data={})
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            message = "Internship Company deleted successfully"
            return response_handler(message = message , code = 200 , data = {})
        except:
            message = "Internship Company no found"
            return response_handler(message=message , code = 400 , data = {})
        
from rest_framework.viewsets import ViewSet
class InternshipReportAPIView(ViewSet):
    parser_classes = [MultiPartParser, FormParser]  # Enable file uploads

    def create_or_update(self, request, *args, **kwargs):
        component = request.data.get("component")
        student = request.data.get("student")
        main_report = request.FILES.get("main_report")  # Can be None
        weekly_file = request.FILES.get("weekly_report")  # Can be None
        week_number = request.data.get("week")  # Required if adding a weekly report
        if not component:
            return Response({"error": "component  is required"}, status=status.HTTP_400_BAD_REQUEST)

        report, created = InternshipReport.objects.get_or_create(
            component_id=component,
            student  = student,
            defaults={"main_report": main_report}
        )

        # Only update main_report if provided (ignore if not sent)
        if main_report:
            # If there's an existing main_report, delete the old file
            if report.main_report:
                old_main_report_path = os.path.join(settings.MEDIA_ROOT, report.main_report.name)
                if os.path.exists(old_main_report_path):
                    os.remove(old_main_report_path)
            
            # Save the new main report
            report.main_report = main_report  

        # Handle weekly file upload
        if weekly_file and week_number:
            # If there's an existing file for this week, delete it
            weekly_files = report.weekly_report if report.weekly_report else {}
            if week_number in weekly_files:
                old_weekly_report_path = os.path.join(settings.MEDIA_ROOT, weekly_files[week_number])
                if os.path.exists(old_weekly_report_path):
                    os.remove(old_weekly_report_path)

            # Save the new weekly file
            path = f"weekly_reports/{weekly_file.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(weekly_file.read())

            # Update the weekly report for the corresponding week
            weekly_files[week_number] = path  # Store { "week1": "file.pdf" }
            report.weekly_report = weekly_files

        report.save()

        return Response(
            InternshipReportSerializer(report).data, 
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )
    

class IntershipStudentWise(APIView):
    def get(self, request , student_id):
        student = get_object_or_404(Student , id = student_id)
        internship_company = InternshipCompany.objects.filter(student = student)
        internship_company = InternshipCompanySerializer(internship_company , many = True)
        return response_handler(message=" intership data fetched successfully" , code = 200 , data = internship_company.data)