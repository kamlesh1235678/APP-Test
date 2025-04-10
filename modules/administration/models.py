from django.db import models
from django.shortcuts import get_object_or_404
from modules.users.models import Student
from django.core.exceptions import ValidationError

# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=150 , unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class Salutation(models.Model):
    name = models.CharField(max_length=50  , unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


class Role(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class Designation(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)



class Batch(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., T-26
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class Terms(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., Term-1
    duration_in_months = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False)

class Specialization(models.Model):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class Course(models.Model):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    duration_in_months =  models.CharField(max_length = 15 , default = 24)

class Subject(models.Model):
    name = models.CharField(max_length=250)
    code  = models.CharField(max_length=10, unique=True)
    credit = models.FloatField()
    description = models.TextField()
    type = models.CharField(max_length= 150,choices=[('Practical','Practical'),('Theory','Theory')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)



class SubjectMapping(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="subject_mappings")
    term = models.ForeignKey(Terms, on_delete=models.PROTECT, related_name="subject_mappings")
    course = models.ManyToManyField(Course, related_name="subject_mappings")
    specialization = models.ManyToManyField(Specialization, related_name="subject_mappings")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="subject_mappings")
    faculty = models.ForeignKey("users.Employee", on_delete=models.PROTECT, related_name="subject_mappings")
    total_classes = models.IntegerField()
    classes_completed = models.IntegerField(default=0)
    weightage_external = models.FloatField()
    weightage_internal = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now= True)
    type = models.CharField(max_length=150 , choices=[("main" , "main") , ("resit-1" , "resit-1") , ("resit-2", "resit-2")])

    @property
    def classes_pending(self):
        return self.total_classes - self.classes_completed

    def __str__(self):
        return f"{self.subject.name} - {self.batch.name} - {self.term.name}"

    class Meta:
        unique_together = ("batch", "subject", "term" , "faculty" , "type")


class StudentMapping(models.Model):
    term = models.ForeignKey(Terms, on_delete=models.PROTECT, related_name="student_mappings")
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT ,  related_name="student_mappings")
    student  = models.ManyToManyField("users.Student" , related_name="student_mappings")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="student_mappings" , null=True , blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="student_mappings" , null=True , blank=True)






class ClassSchedule(models.Model):
    mapping = models.ForeignKey(SubjectMapping , on_delete=models.PROTECT , related_name="schedules")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_complete = models.BooleanField(default=False)
    is_cancel = models.BooleanField(default= False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now= True)
    

    def __str__(self):
        return f"{self.mapping.subject.name} - {self.date}"
    
    def check_conflicts(self):
        """Returns a list of validation errors instead of raising exceptions."""
        errors = []

        # Faculty Conflict Check
        faculty = self.mapping.faculty
        overlapping_classes = ClassSchedule.objects.filter(
            mapping__faculty=faculty,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            is_complete = False,
            is_cancel = False
        ).exclude(id=self.id)

        if overlapping_classes.exists():
            errors.append("Faculty has another class scheduled at this time.")

        # Event Conflict Check
        event_on_same_day = Events.objects.filter(date__date=self.date).exists()
        if event_on_same_day:
            errors.append("Cannot schedule class on an event day.")

        return errors
    
    def save(self, *args , **kwargs):
        errors = self.check_conflicts()
        if errors:
            raise Exception({"errors": errors})
        pervious = None
        if self.pk:
            pervious = ClassSchedule.objects.get(id = self.pk)
        super().save(*args, **kwargs)
        if pervious and not pervious.is_complete and self.is_complete:
            classes_completed = self.mapping.classes_completed + 1
            SubjectMapping.objects.update_or_create(pk=self.mapping.id, defaults= {'classes_completed':classes_completed})
        # to persent direct leave approved student
        if not self.is_cancel:
            approved_leaves = StudentLeaveRequest.objects.filter(
                start_date__lte=self.date, end_date__gte=self.date, status="Approved"
            )
            # import pdb;pdb.set_trace()
            class_schedule = get_object_or_404(ClassSchedule , id = self.pk)
            # import pdb;pdb.set_trace()
            course = class_schedule.mapping.course.all()
            batch = class_schedule.mapping.batch
            term =  class_schedule.mapping.term
            specialization= class_schedule.mapping.specialization.all()
            students = Student.objects.filter(course__in = course , batch = batch , student_mappings__term = term , student_mappings__specialization__in = specialization ).distinct().values_list('id',flat=True)
            # import pdb;pdb.set_trace()
            
            for leave in approved_leaves:
                if leave.student.pk in students:
                    Attendance.objects.update_or_create(
                        student=leave.student,
                        class_schedule=self,
                        defaults={'is_persent': True}
                    )
        else:
            Attendance.objects.filter(class_schedule=self.pk).delete()



    
class Attendance(models.Model):
    class_schedule = models.ForeignKey(ClassSchedule , on_delete= models.PROTECT , related_name="attendances")
    student = models.ForeignKey("users.Student" ,on_delete= models.PROTECT , related_name="attendances" )
    is_persent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateTimeField(auto_now= True)
    ce_marks = models.FloatField(default=0)

    class Meta:
        unique_together = ("class_schedule" , "student")

    def __str__(self):
        return f"{self.class_schedule.mapping.subject.name} - {self.student.user.email}"
    



class Component(models.Model):
    subject_mapping = models.ForeignKey(SubjectMapping, on_delete=models.PROTECT, related_name="components")
    type = models.CharField(max_length=150, choices=[('INTERNAL', 'Internal'), ('EXTERNAL', 'External')])
    name = models.CharField(max_length=250)  # e.g., "Assignment", "Midterm , Final"
    max_marks = models.FloatField(default=0)  
    has_subcomponents = models.BooleanField(default=False)
    description = models.TextField(null = True , blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(null=True, blank=True)  
    end_date = models.DateTimeField(null=True, blank=True)
    is_submission = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)



class SubComponent(models.Model):
    component = models.ForeignKey(Component, on_delete=models.PROTECT, related_name="subcomponents")
    name = models.CharField(max_length=250)  # e.g., "Assignment 1", "Assignment 2"
    max_marks = models.FloatField()
    description = models.TextField(null = True , blank= True)
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateTimeField(auto_now= True)
    start_date = models.DateTimeField(null=True, blank=True)  
    end_date = models.DateTimeField(null=True, blank=True)
    is_submission = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    


class Exam(models.Model):
    component = models.ForeignKey(Component , models.PROTECT , related_name="exam_subject")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_cancel = models.BooleanField(default= False)
    is_reschedule = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateTimeField(auto_now= True)

    def __str__(self):
        return f"{self.component.subject_mapping}  - {self.date}"


class ComponentMarks(models.Model):
    student = models.ForeignKey('users.Student', on_delete=models.PROTECT, related_name="component_marks")
    component = models.ForeignKey(Component, related_name="component_marks", on_delete=models.PROTECT)
    obtained_marks = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_passed(self):
        return self.obtained_marks >= (0.5 * self.component.max_marks)


class SubComponentMarks(models.Model):
    student = models.ForeignKey('users.Student', on_delete=models.PROTECT, related_name="subcomponent_marks")
    subcomponent = models.ForeignKey(SubComponent, related_name="subcomponent_marks", on_delete=models.PROTECT)
    obtained_marks = models.FloatField()
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateTimeField(auto_now= True)

    def save(self, *args, **kwargs):
        """ When subcomponent marks are updated, update the ComponentMarks """
        super().save(*args, **kwargs)
        component = self.subcomponent.component
        total_obtained = component.subcomponents.aggregate(total=models.Sum('subcomponent_marks__obtained_marks'))['total'] or 0
        ComponentMarks.objects.update_or_create(student=self.student, component=component, defaults={'obtained_marks': total_obtained})


class ResetExamRequest(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="resets")
    term = models.ForeignKey(Terms, on_delete=models.PROTECT, related_name="resets")
    course = models.ForeignKey(Course , on_delete= models.PROTECT  , related_name= 'resets')
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT ,  related_name="resets")
    student = models.ForeignKey("users.Student", on_delete=models.PROTECT , related_name="resets")
    subjects = models.ForeignKey(SubjectMapping ,on_delete=models.PROTECT, related_name="resets" )
    status = models.CharField(max_length=20, choices=[("Pending", "Pending"), ("Approved", "Approved")], default="Pending")
    type = models.CharField(max_length=150  , choices=[("resit-1" , "resit-1") ,("resit-2" , "resit-2")])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.first_name}-{self.subjects.subject.name}"
    
    # class Meta:
    #     unique_together = ("batch", "subjects", "term"  , "type" , 'course' , 'student' , 'specialization')
    


class ComponentAnswers(models.Model):
    component = models.ForeignKey(Component, related_name="component_answer", on_delete=models.PROTECT)
    answers_file = models.TextField()
    student = models.ForeignKey('users.Student', on_delete=models.PROTECT, related_name="component_answer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class InternshipCompany(models.Model):
    subject_mapping = models.ForeignKey(SubjectMapping, on_delete=models.PROTECT, related_name="intership")
    student = models.ForeignKey('users.Student', on_delete=models.PROTECT, related_name="intership")
    company_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date  = models.DateField()
    mentor_name = models.CharField(max_length=200)
    mentor_mobile_number = models.CharField(max_length=13)
    location = models.TextField()
    offer_letter = models.FileField(upload_to='internship_offer_letter')
    campus_joining_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class InternshipReport(models.Model):
    component = models.ForeignKey(Component, on_delete=models.PROTECT, related_name="intern_report" , null=True , blank= True)
    main_report = models.FileField(upload_to="internship_reports/" , null=True , blank= True)
    weekly_report = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student = models.ForeignKey('users.Student', on_delete=models.PROTECT, related_name="intern_report" , null = True , blank=True)





class NoticeBoard(models.Model):
    title = models.CharField(max_length=1999)
    date = models.DateField()
    description = models.TextField()
    valid_date = models.DateField()
    user = models.ForeignKey("users.Employee" , on_delete=models.PROTECT , related_name="notice_board")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to='notice_board/' , null=True , blank=True)

    def __str__(self):
        return self.title
    
class StudentLeaveRequest(models.Model):
    student = models.ForeignKey("users.Student", on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    student_reason  = models.TextField()
    status = models.CharField(max_length=10, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
    status_description  = models.TextField(null=True , blank= True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.start_date}-{self.end_date}"
    

class SubjectMappingSyllabus(models.Model):
    mapping = models.ForeignKey(SubjectMapping , on_delete= models.PROTECT  , related_name="subject_syllabus")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

class SubComponentAnswers(models.Model):
    sub_component = models.ForeignKey(SubComponent, related_name="subcomponent_answer", on_delete=models.PROTECT)
    answers_file = models.TextField()
    student = models.ForeignKey('users.Student', on_delete=models.PROTECT, related_name="subcomponent_answer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class Events(models.Model):
    name = models.CharField(max_length=450)
    date = models.DateTimeField()
    venue =  models.CharField(max_length=999)
    type =  models.CharField(max_length=999)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum

@receiver(post_save, sender=Attendance)
def update_component_marks(sender, instance, **kwargs):
    try:
        subject = instance.class_schedule.mapping
        student = instance.student

        # Get the "CE" component for this subject
        ce_component = Component.objects.get(name="CE", subject_mapping=subject)


        # Sum all ce_marks for this student and subject
        total_ce_marks = Attendance.objects.filter(
            class_schedule__mapping=subject,
            student=student
        ).aggregate(total=Sum("ce_marks"))["total"] or 0

        # Update or create ComponentMarks
        ComponentMarks.objects.update_or_create(
            student=student,
            component=ce_component,
            defaults={"obtained_marks": total_ce_marks}
        )
    except Component.DoesNotExist:
        pass
