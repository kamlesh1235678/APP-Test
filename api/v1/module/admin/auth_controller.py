import random
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import update_last_login
from django.contrib.auth import authenticate
from api.v1.module.serializers.auth_serializer import *
from api.v1.module.response_handler import response_handler
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password , check_password
from modules.users.models import *
from rest_framework import status

class LoginAPIView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username', '').strip().lower()
        password = request.data.get('password', '')
        
        if not username or not password:
            return response_handler(message = "Please provide both username and password" , code = 400 , data = {})
        user = authenticate(username=username, password=password)
        if user is not None:
            if not user.is_active:
                return response_handler(message="Your account is Inactive. Please contact the administrator.", code=400, data={})
            if user.is_lock:
                return response_handler(message="Your account is Locked. Please contact the administrator.", code=400, data={})
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            update_last_login(None, user)
            return response_handler(message = "Login successfully done" , code = 200 , data = {'access_token': access_token,'refresh_token':refresh_token,'permission_list' :LoginSerializer(user).data['permission_list'] , 
                'user': LoginSerializer(user).data,})
        else:
            return response_handler(message = "Invalid username or password." , code = 400 , data = {})

class LogoutAPIView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return response_handler(message = "Refresh token is required." , code = status.HTTP_400_BAD_REQUEST , data = {})
            
            token = RefreshToken(refresh_token)
            token.blacklist()  # Blacklist the token to prevent reuse
            
            return response_handler(message = "Logout successful." , code = status.HTTP_200_OK , data = {})
        except Exception as e:
            return response_handler(message = "Invalid token." , code = status.HTTP_400_BAD_REQUEST , data = {})

class SendOtpAPIView(APIView):
  permission_classes = (AllowAny,)
  def post(self,request):
    username = request.data.get('username',None)
    users = User.objects.filter(Q(Q(email = username) & Q(is_lock=False)) & Q(is_active=True))
    # import pdb; pdb.set_trace()
    if users.exists():
      otp = random.randint(1000,9999)
      user_obj = users.first()
      otp_obj , created  = UserOtp.objects.update_or_create(user=user_obj, defaults={"otp": otp})
    #   import pdb; pdb.set_trace()
      user_data = {'user':user_obj.id,'otp':otp_obj.otp}
    #   subject = 'Taxila Busiess School Forget Password Otp'
    #   message = str(otp)
    #   email_from = settings.EMAIL_HOST_USER
    #   recipient_list = [username]
    #   send_mail(subject, message, email_from, recipient_list)
      message ="Otp send successfully for forget password, Please check your email"
      return response_handler(code=200,message=message,data=user_data )
    message = "User not found," 
    return response_handler(code=400,message=message,data={})
  


class VerifyOtpAPIView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        username = request.data.get('username', None)
        otp = request.data.get('otp', None)
        if not username or not otp:
            return response_handler(code=400, message="Email or OTP is missing", data={})
        try:
            user = User.objects.get(Q(Q(email=username) & Q(is_lock=False)) & Q(is_active=True))
            user_otp = UserOtp.objects.get(user=user, otp=otp)
        except User.DoesNotExist:
            return response_handler(code=400, message="User not found", data={})
        except UserOtp.DoesNotExist:
            return response_handler(code=400, message="Invalid OTP", data={})
        
        # OTP verified successfully
        user_otp.delete()  # Optionally delete the OTP after successful verification
        return response_handler(code=200, message="OTP verified successfully", data={'user_id': user.id , 'username':username})


class ForgetPasswordAPIView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        username = request.data.get('username', None)
        new_password = request.data.get('new_password', None)
        confirm_password = request.data.get('confirm_password', None)
        
        if not username or not new_password or not confirm_password:
            return response_handler(code=400, message="Email, new password, or confirm password is missing", data={})
        
        if new_password != confirm_password:
            return response_handler(code=400, message="New password and confirm password do not match", data={})
        
        try:
            user = User.objects.get(Q(Q(email=username) & Q(is_lock=False)) & Q(is_active=True))
        except User.DoesNotExist:
            return response_handler(code=400, message="User not found", data={})
        
        user.password = make_password(new_password)
        user.save()
        
        return response_handler(code=200, message="Password reset successfully", data={'user_id': user.id})

# class AuditLogAPIView(APIView):
#     def get(self, request):
#         queryset = AuditLog.objects.all().order_by('-id')
#         serializer = AuditLogSerializer(queryset , many = True)
#         return response_handler(message="Logs listh fetched successfully" , code = 200 , data = serializer.data)
    
from rest_framework.pagination import PageNumberPagination
class AuditLogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    # max_page_size = 100

class AuditLogAPIView(APIView):
    def get(self, request):
        queryset = AuditLog.objects.all().order_by('-id')
        paginator = AuditLogPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = AuditLogSerializer(result_page, many=True)
        return response_handler(message="Logs listh fetched successfully" , code = 200 , data = serializer.data)
    


class ResetPasswordAPIView(APIView):
    def post(self, request):
        current_password = request.data.get('current_password', None)
        new_password = request.data.get('new_password', None)
        confirm_password = request.data.get('confirm_password', None)

        # Ensure the current password and new password are provided
        if not current_password or not new_password or not confirm_password:
            return response_handler(message="Current password, new password, or confirm password is missing" , code=400 , data = {})
            

        # Ensure new password and confirm password match
        if new_password != confirm_password:
            return response_handler(message = "New password and confirm password do not match" , code=400 , data={})

        # Check if the provided current password matches the one stored in the database
        if not check_password(current_password, request.user.password):
            return response_handler(message="Current password is incorrect" , code = 400 , data={})

        # Update the user's password with the new one
        request.user.password = make_password(new_password)
        request.user.save()

        return response_handler(message="Password reset successfully" , code = 200 , data={})