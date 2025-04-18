from django.http import JsonResponse
from django.urls import path, re_path, include
from api.v1.module.admin.student_controller import *
from api.v1.module.admin.employee_controller import *
from api.v1.module.admin.department_controller import *
from api.v1.module.admin.designation_controller import *
from api.v1.module.admin.role_controller import *
from api.v1.module.admin.salutation_controller import *
from api.v1.module.admin.auth_controller import *
from api.v1.module.admin.batch_controller import *
from api.v1.module.admin.course_controller import *
from api.v1.module.admin.subject_controller import *
from api.v1.module.admin.terms_controller import *
from api.v1.module.admin.specialization_controller import *
from api.v1.module.admin.class_controller import *
from api.v1.module.admin.exam_controller import *
from api.v1.module.admin.permission_controller import *
from api.v1.module.admin.component_controller import *
from api.v1.module.admin.profile_controller import *
from api.v1.module.admin.subject_mapping_controller import *
from api.v1.module.admin.student_mapping_controller import *
from api.v1.module.admin.resit_controller import *
from api.v1.module.admin.mix_controller import *
from api.v1.module.admin.internship_controller import *
from api.v1.module.admin.noticeboard_controller import *
from api.v1.module.admin.leave_controller import *
from api.v1.module.admin.events_controller import *
from api.v1.module.admin.admit_card_controller import *


from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import routers
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'student-viewset',StudentModelViewSet)
router.register(r'employee-viewset',EmployeeModelViewSet)
router.register(r'department-viewset',DepartmentModelViewSet)
router.register(r'designation-viewset',DesignationModelViewSet)
router.register(r'salutation-viewset',SalutationModelViewSet)
router.register(r'role-viewset',RoleModelViewSet)
router.register(r'batch-viewset',BatchModelViewSet)
router.register(r'terms-viewset',TermsModelViewSet)
router.register(r'specialization-viewset',SpecializationModelViewSet)
router.register(r'course-viewset',CourseModelViewSet)
router.register(r'subject-viewset',SubjectModelViewSet)
router.register(r'subject-mapping-viewset',SubjectMappingModelViewSet)
router.register(r'class-schedule-viewset',ClassScheduledModelViewSet)
router.register(r'student-mapping-viewset',StudentMappingModelViewSet)
router.register(r'exam-viewset',ExamModelViewSet)
router.register(r'permission-viewset',PermissionModelViewSet)
router.register(r'component-viewset',ComponentModelViewSet)
router.register(r'resit-viewset',ResetExamRequestModelViewSet)
router.register(r'student-documet-viewset',StudentDocumentModelSetView)
router.register(r'component-answer-viewset',ComponentAnswersModelViewSet)
router.register(r'membership-viewset',FacultyMentorshipModelViewSet)
router.register(r'intership-company-viewset',InternshipCompanyModelViewSet)
router.register(r'noticeboard-viewset' , NoticeBoardModelViewSet)
router.register(r'student-leave-viewset' , StudentLeaveRequestModelViewSet)
router.register(r'subject-syllabus-viewset' , SubjectMappingSyllabusModelViewSet)
router.register(r'sub-component-answer-viewset' , SubComponentAnswersModelViewSet)
router.register(r'events-viewset' , EventsModelViewSet)
router.register(r'hall-ticket-viewset' , HallTicketAnnounceModelViewSet)


def base_view(request):
    return JsonResponse({"message": "Backend running successfully"})

urlpatterns = [
  path('', base_view, name='base-view'),
  path('', include(router.urls)),
  path('login', LoginAPIView.as_view() , name = "login"),
  path('mark-attendance/<int:class_id>', ClassAttendanceAPIView.as_view() , name = "mark-attendance"),
  path('assign-permissions/<int:role_id>', RolePermissionAPIView.as_view() , name = "assign-permissions"),
  path('sub-component/<int:component_id>', SubComponentAPIView.as_view() , name = "sub-component"),
  path('component-marks/<int:component_id>', ComponentMarksAPIView.as_view() , name = "component-marks"),
  path('sub-component-marks/<int:subcomponent_id>', SubComponentMarksAPIView.as_view() , name = "sub-component-marks"),
  path('subject-attendance/<int:subject_mapping_id>', SubjectAttendanceListAPIView.as_view() , name = "subject-attendance"),
  path('student-profile', StudentProfileAPIView.as_view() , name = "student-profile"),
  path('employee-profile', EmployeeProfileAPIView.as_view() , name = "employee-profile"),
  path('choose-specialization/<int:term_id>', StudentSpecializationAPIView.as_view() , name = "choose-specilaization"),
  path('student-gpa/<int:student_id>/<int:batch_id>/<int:course_id>/<int:term_id>', StudentMainSubjectWiseGPAAPIView.as_view() , name = "student-gpa"),
  path('resit-component-marks/<int:component_id>' , ResetStudentComponentMarksUpdateAPI.as_view() , name = "resit-component-marks"),
  path('resit-student-gpa/<int:student_id>/<int:batch_id>/<int:course_id>/<int:term_id>', StudentReset1SubjectWiseGPAAPIView.as_view() , name = "resit-student-gpa"),
  path('send-otp', SendOtpAPIView.as_view(), name='send-otp'),
  path('verify-otp', VerifyOtpAPIView.as_view(), name='verify-otp'),
  path('forget-password', ForgetPasswordAPIView.as_view(), name='forget-password'),
  path('logout' , LogoutAPIView.as_view() , name = "logout"),
  path('token/refresh', TokenRefreshView.as_view(), name="token_refresh"),
  path('all-entities', MixAPIView.as_view(), name="all-entities"),
  path('batches-list', BatchSingleListAPIView.as_view(), name='batches-list'),
  path('terms-list', TermsSingleListAPIView.as_view(), name='terms-list'),
  path('courses-list', CourseSingleListAPIView.as_view(), name='courses-list'),
  path('subjects-list', SubjectSingleListAPIView.as_view(), name='subjects-list'),
  path('specializations-list', SpecializationSingleListAPIView.as_view(), name='specializations-list'),
  path('bulk-subject-mapping', BulkSubjectMappingCreateView.as_view(), name='bulk-subject-mapping'),
  path('student-upload' , UploadStudentExcel.as_view() , name = "student-upload"),
  path('intership-report' , InternshipReportAPIView.as_view({"post": "create_or_update"}), name = "intership-report"),
  path('log-list' , AuditLogAPIView.as_view(), name = "log-list"),
  path('subject-mapping-filter' , SubjectMappingSingleListAPIView.as_view(), name = "subject-mapping-filter"),
  path('bulk-class-schedule' , BulkClassScheduledAPIView.as_view(), name = "bulk-class-schedule"),
  path('component-filter' , ComponentFilterAPIView.as_view(), name = "component-filter"),
  path('assign-faculty-filter' , FAcultyFilterAPIView.as_view(), name = "assign-faculty-filter"),
  path('employee-list' , EmployeeSingleListAPIView.as_view(), name = "employee-list"),
  path('student-list' , StudentSingleListAPIView.as_view(), name = "student-list"),
  path('student-promote' , PromoteStudentInTermAPIView.as_view(), name = "student-promote"),
  path('students/no-mentor' , MembershipFilterAPIView.as_view(), name = "students/no-mentor"),
  path('employee-upload' , UploadEmployeeExcel.as_view(), name = "employee-upload"),
  path('student-view/<int:pk>' , StudentDetailAPIView.as_view(), name = "student-view"),
  path('faculty-wise-class/<int:faculty_id>' , ScheduleClassFacultyWise.as_view(), name = "faculty-wise-class"),
  path('attendance-summary/<int:student_id>/<int:days>' , AttendanceSummary.as_view(), name = "attendance-summary"),
  path('component-subject-wise/<int:subject_id>' , ComponentSubjectWise.as_view(), name = "component-subject-wise"),
  path('subcomponent-component-wise/<int:component_id>' , SubComponentComponentWise.as_view(), name = "subcomponent-component-wise"),
  path('class-subject-wise/<int:subject_id>' , ScheduleclassSubjectWise.as_view(), name = "class-subject-wise"),
  path('student-marks-subject-wise/<int:student_id>/<int:subject_id>' , ComponentMarksSubjectWiseSummary.as_view(), name = "student-marks-subject-wise"),
  path('subject-student-wise/<int:student_id>' , SubjectStudentWise.as_view(), name = "subject-student-wise"),
  path('subcomponents-action/<int:sub_component_id>', SubcomponentViewUpdateAPIView.as_view(), name='subcomponent-detail-update'),
  path('student-component-answer/<int:component_id>', StudentComponentAnswer.as_view(), name='student-component-answer'),
  path('student-subcomponent-answer/<int:subcomponent_id>', StudentSubComponentAnswer.as_view(), name='student-subcomponent-answer'),
  path('student-subcomponent-answer-details/<int:student_id>/<int:subcomponent_id>', StudentSubComponentAnswerDetails.as_view(), name='student-subcomponent-answer-details'),
  path('student-component-answer-details/<int:student_id>/<int:component_id>', StudentComponentAnswerDetails.as_view(), name='student-component-answer-details'),
  path('count', DashBoardCountAPIView.as_view(), name='count'),
  path('intership-student-wise/<int:student_id>', IntershipStudentWise.as_view(), name='intership-student-wise'),
  path('subject-mapping-syllabus/<int:subject_mapping_id>', SubjectMappingSyllabusAPI.as_view(), name='subject-mapping-syllabus'),
  path('attendance-summary-filter/<int:student_id>', AttendanceSummaryFilter.as_view(), name='attendance-summary-filter'),
  path('student-wise-class/<int:student_id>', UpComeingStudentClassAPIView.as_view(), name='student-wise-class'),
  path('exam-subject-wise/<int:subject_id>', ExamSubjectWiseAPIView.as_view(), name='exam-subject-wise'),
  path('dashboard-student-data/<int:student_id>', DashBoardStudentDataAPIView.as_view(), name='dashboard-student-data'),
  path('faculty-wise-class-filter/<int:faculty_id>', UpComeingFacultyClassAPIView.as_view(), name='faculty-wise-class-filter'),
  path('student-mapping-filter', StudentMappingFilter.as_view(), name='student-mapping-filter'),
  path('employee-details/<int:faculty_id>', EmployeeSummary.as_view(), name='employee-details'),
  path('reset-password', ResetPasswordAPIView.as_view(), name='reset-password'),
  path('admit-card', AdmitCardView.as_view(), name='admit-card'),
  path('hall-ticket/<int:student_id>/<int:term_id>', HallTicketWise.as_view(), name='hall-ticket'),
  path('class-subject-wise-filter/<int:subject_id>' , UpComeingSubjectMappingClassAPIView.as_view(), name = "class-subject-wise-filter"),
  path('subject-exam-schedule-bulk' , ExamSubjectMappingListAPIView.as_view() , name = "subject-exam-schedule-bulk")
]

                                                                                                                                                                                         


                                                                                                                                                                                         