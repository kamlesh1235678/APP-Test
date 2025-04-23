from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not extra_fields.get('user_type'):
            raise ValueError("The user_type field must be set")
        
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    STUDENT = 'STUDENT'
    EMPLOYEE = 'EMPLOYEE'
    USER_TYPE = (
        (STUDENT, 'Student'),
        (EMPLOYEE, 'Employee')
    )

    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=150, choices=USER_TYPE)
    is_staff = models.BooleanField(default=False)  
    is_superuser = models.BooleanField(default=False)  
    is_active = models.BooleanField(default=False)
    is_lock = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type']

    def __str__(self):
        return self.email
    
    @property
    def role(self):
        """Get the role dynamically from related Student or Employee"""
        if hasattr(self, 'student'):
            return self.student.student_role.name
        elif hasattr(self, 'employee'):
            return self.employee.employee_role.name
        return None


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    # Personal Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=3 , null=True , blank=True)
    date_of_birth = models.DateField()
    aadhar_number = models.CharField(max_length=12, unique=True , null=True , blank=True)
    # Education Details
    tenth_score_type = models.CharField(max_length=10, choices=[('CGPA', 'CGPA'), ('Percentage', 'Percentage')] , null=True , blank=True)
    tenth_score = models.FloatField(null=True , blank=True)
    twelfth_score_type = models.CharField(max_length=10, choices=[('CGPA', 'CGPA'), ('Percentage', 'Percentage')] , null=True , blank=True)
    twelfth_score = models.FloatField(null=True , blank=True)
    graduation_background = models.CharField(max_length=100 , null=True , blank=True)
    graduation_score_type = models.CharField(max_length=10, choices=[('CGPA', 'CGPA'), ('Percentage', 'Percentage')] , null=True , blank=True)
    graduation_score = models.FloatField(null=True , blank=True)
    # roll Details
    date_of_joining = models.DateField(null=True , blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    category = models.CharField(max_length=50 , null=True , blank=True)
    entrance_score_card = models.TextField(null=True , blank=True)
    experience_status = models.BooleanField(null=True , blank=True)
    # Address
    address = models.TextField(null=True , blank=True)
    city = models.CharField(max_length=100 , null=True , blank=True)
    state = models.CharField(max_length=100 , null=True , blank=True)
    pincode = models.CharField(max_length=10 , null=True , blank=True)
    # Father's Information
    father_name = models.CharField(max_length=100 , null=True , blank=True)
    father_contact_number = models.CharField(max_length=15 , null=True , blank=True)
    father_email = models.EmailField(blank=True, null=True)
    father_aadhar_number = models.CharField(max_length=12, unique=True,  null=True , blank=True)
    # Mother's Information
    mother_name = models.CharField(max_length=100 , null=True , blank=True)
    mother_contact_number = models.CharField(max_length=15 , null=True , blank=True)
    mother_email = models.EmailField(blank=True, null=True)
    mother_aadhar_number = models.CharField(max_length=12, unique=True , null=True , blank=True)
    #archived
    is_archived = models.BooleanField(default=False)
    #batch
    batch = models.ForeignKey('administration.Batch' , on_delete=models.PROTECT, related_name='student_batch')
    student_role = models.ForeignKey('administration.Role', on_delete=models.PROTECT)
    course = models.ForeignKey('administration.Course' , on_delete=models.PROTECT, related_name='student_course')
    #experience details
    experience_details = models.JSONField(default= list) #Example format: [{"company_name": "XYZ Corp", "experience_in_months": 24, "industry": "IT Solution and Products"}]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #some more data according aicte
    enrollment_number = models.CharField(max_length=20 , unique=True , null=True , blank=True )
    aicte_permanent_id = models.CharField(max_length=20 , unique=True , null=True , blank=True )
    religion = models.CharField(max_length=50 , null=True , blank=True)
    district  = models.CharField(max_length=100 , null=True , blank=True)
    pwd = models.BooleanField(default=False ,null=True, blank=True)
    dropped = models.BooleanField(default=False ,null=True, blank=True)
    passout_status = models.BooleanField(default=False ,null=True, blank=True)

    entrance_appear = models.CharField(max_length=30 , null = True , blank= True)
    entrance_appear_year = models.CharField(max_length=10  , null=True , blank= True)

    
    def total_exprience(self):
        if not isinstance(self.experience_details, list):
            return 0
        else:
            return sum(((exp.get("experience_in_months", 0))/12) for exp in self.experience_details)
        
    # def save(self, *args, **kwargs):
    #     if not self.roll_number and self.batch:
    #         year = self.batch.start_date.year
    #         last_roll = Student.objects.filter(batch__start_date__year=year).order_by('-id').first()
    #         next_number = 1 if not last_roll else int(last_roll.roll_number[-3:]) + 1
    #         self.roll_number = f"PGDM{year}{next_number:03d}"
    #     super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT , related_name="employee")
    # Basic Details
    salutation = models.ForeignKey('administration.Salutation', on_delete=models.PROTECT)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    contact_no = models.CharField(max_length=15, unique=True)  
    aadhar_no = models.CharField(max_length=12, unique=True , null=True , blank=True) 
    pan_no = models.CharField(max_length=10, unique=True , null=True , blank=True)  
    biometric_id = models.CharField(max_length=20, unique=True ,  null=True , blank=True) 
    blood_group = models.CharField(max_length=3 ,  null=True , blank=True)
    # Dates
    date_of_birth = models.DateField()
    date_of_joining = models.DateField( null=True , blank=True)
    # Employment Details
    institute_department = models.ForeignKey('administration.Department', on_delete=models.PROTECT, null=True , blank=True)
    designation = models.ForeignKey('administration.Designation', on_delete=models.PROTECT, null=True , blank=True)
    employee_role = models.ManyToManyField('administration.Role' , related_name="employees_roles")
    # Address Details
    address = models.TextField( null=True , blank=True)
    city = models.CharField(max_length=50 ,  null=True , blank=True)
    state = models.CharField(max_length=50 ,  null=True , blank=True)
    pincode = models.CharField(max_length=6 ,  null=True , blank=True)  
    #archived
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # extra details
    employee_type = models.CharField(max_length=20 , choices=[("Teaching" , "Teaching") ,("Non-Teaching" ,"Non-Teaching")] ,  null=True , blank= True)
    education = models.JSONField(default=list)  # List of education records
    experience = models.JSONField(default=list)  # List of work experiences
    publications = models.JSONField(default=list)  # List of publications
    conferences = models.JSONField(default=list)  # List of conferences attended
    achievements = models.JSONField(default=list)  # List of achievements
    interest = models.JSONField(default=list)  # List of interests
    articles = models.JSONField(default=list)  # List of articles
    additional_details = models.JSONField(default=list) # List of additional 
    
    # other detail according aicte
    father_name = models.CharField(max_length=100 , null=True , blank= True)
    mother_name  = models.CharField(max_length=100 , null=True , blank= True)
    appointment_type = models.CharField(max_length=50 , null=True , blank= True)
    teaching_exprience = models.FloatField(null=True , blank= True)
    research_exprience = models.FloatField(null=True , blank= True)
    industry_exprience = models.FloatField(null=True , blank= True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.designation}"
    


class UserOtp(models.Model):
    user = models.ForeignKey(User  , on_delete=models.PROTECT , related_name="user_otp")
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class StudentDocument(models.Model):
    student = models.ForeignKey(Student , on_delete=models.PROTECT , related_name="Student_document")
    document_name = models.CharField(max_length=150)
    document_file = models.FileField(upload_to='student_document/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class StudentFeeStatus(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT , related_name="student_fee")
    form_fee = models.BooleanField(default=False) #form fee status
    program_fee_paid = models.BooleanField(default=False)  # Course fee installment status
    enrollment_fee_paid = models.BooleanField(default=False)  # Enrollment fee status
    caution_fee_tuition = models.BooleanField(default=False)  # Caution fee status
    extra_penalty = models.BooleanField(default=False)  # Penalty status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class FacultyMentorship(models.Model):
    user = models.ForeignKey(Employee, on_delete=models.PROTECT , related_name="faculty_membership")
    students = models.ManyToManyField(Student , related_name="faculty_membership")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.faculty} Mentorship"
    


class AuditLog(models.Model):
    ACTIONS = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    model_name = models.CharField(max_length=255)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTIONS)
    changes = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    request_url = models.URLField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.action} {self.model_name} {self.object_id}"