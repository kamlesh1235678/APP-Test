import json
from .models import AuditLog
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from modules.privacy.models import RolePermission
from api.v1.module.response_handler import *


class APILogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Manually authenticate user using DRF JWTAuthentication
        jwt_authenticator = JWTAuthentication()
        
        try:
            # Authenticate and set user in request
            auth_result = jwt_authenticator.authenticate(request)
            if auth_result is not None:
                request.user, _ = auth_result  # Set authenticated user
            else:
                request.user = AnonymousUser()  # Keep as anonymous if no token

        except Exception as e:
            request.user = AnonymousUser()  # Ensure request.user is always set
        
        # Debugging: Print the authenticated 
        # import pdb; pdb.set_trace()
        if request.user and request.user.is_authenticated:
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:  # Only log for modifying methods
                request_url = request.build_absolute_uri()  # Full URL
                ip_address = request.META.get('REMOTE_ADDR')

                if request.content_type and 'multipart/form-data' in request.content_type:
                    # If the request contains files, use request.FILES and request.POST
                    body_data = request.POST.dict()  # Convert QueryDict to dict
                    body_data['files'] = {key: file.name for key, file in request.FILES.items()}
                else:
                    # Handle normal JSON requests
                    try:
                        body_data = json.loads(request.body.decode('utf-8'))
                    except (json.JSONDecodeError, AttributeError):
                        body_data = {}

                # Determine the action
                if request.method == "POST":
                    if request.resolver_match and "pk" in request.resolver_match.kwargs:
                        action = "UPDATE"  # POST with pk -> Update
                    else:
                        action = "CREATE"  # POST without pk -> Create
                elif request.method in ["PUT", "PATCH"]:
                    action = "UPDATE"
                elif request.method == "DELETE":
                    action = "DELETE"

                AuditLog.objects.create(
                    user=request.user,
                    model_name="API Request",
                    object_id=request.resolver_match.kwargs.get("pk", None) if request.resolver_match and request.resolver_match.kwargs else None,
                    action=action,
                    changes=json.dumps(body_data) if body_data else None,
                    request_url=request_url,
                    ip_address=ip_address
                )
           
        


PERMISSION_MAP = {
        '/admin/product-edit/': 'change_product', 
        '/admin/product-add/': 'add_product',   
        '/admin/product-delete/': 'delete_product', 
        '/admin/product-view/': 'view_product',  
        '/admin/product-list/': 'list_product', 
        '/admin/category-edit/': 'change_category', 
        '/admin/category-add/': 'add_category',   
        '/admin/category-delete/': 'delete_category', 
        '/admin/category-view/': 'view_category',   
        '/admin/subcategory-edit/': 'change_subcategory', 
        '/admin/subcategory-add/': 'add_subcategory',   
        '/admin/subcategory-delete/': 'delete_subcategory', 
        '/admin/subcategory-view/': 'view_subcategory',  
        '/admin/banner-edit/': 'change_banner', 
        '/admin/banner-add/': 'add_banner',   
        '/admin/banner-delete/': 'delete_banner', 
        '/admin/banner-view/': 'view_banner',  
        '/admin/employee-edit/': 'change_user', 
        '/admin/employee-add/': 'add_user',   
        '/admin/employee-delete/': 'delete_user', 
        '/admin/employee-view/': 'view_user', 
        '/admin/employee-list/': 'list_user', 
        '/admin/cms-edit/': 'change_cms', 
        '/admin/cms-add/': 'add_cms',   
        '/admin/cms-delete/': 'delete_cms', 
        '/admin/cms-view/': 'view_cms',
        '/admin/product-approval-list/': 'list_product_approval', 
        '/admin/vendor-approval-list/': 'list_vender_approval',
        '/admin/vendor-list/': 'list_vender',
        '/admin/banner-list/': 'list_banner',
        '/admin/notes-list/': 'list_notes',
        '/admin/cms-list/': 'list_cms',
        '/admin/permission-staff/': 'list_staff',
        '/admin/permission-manager/': 'list_manager',
        '/admin/category-list/': 'list_category',
        # Add more mappings as needed
        '/admin/banner-active/': 'active_banner',
        '/admin/vendor-approval-action/' : 'approval_user',
        '/admin/product-approval-action/' : 'approval_product',
    }
    
class PermissionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            requested_path = request.path
            role = request.user.role
            if request.user.is_superuser:
                return None
            # Iterate over the permission map to check for permissions
            for base_path, permission_codename in PERMISSION_MAP.items():
                if base_path in requested_path:
                    # Check if the user has the required permission
                    has_permission = RolePermission.objects.filter(
                        role = role,
                        permission__codename=permission_codename
                    ).exists()
                    # If the user does not have permission, redirect to the unauthorized page
                    if not has_permission:
                        return response_handler(message="You have not Access of Given Option" , code = 401 , data = {})
        return None
