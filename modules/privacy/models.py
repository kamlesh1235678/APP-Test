from django.db import models
from modules.administration.models import Role
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save , post_delete
from django.dispatch import receiver
# Create your models here.



class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="role_permissions")
    permission = models.ManyToManyField(Permission  , related_name="role_permissions")



@receiver(post_save, sender=Role)
def create_role_permission(sender, instance, created, **kwargs):
    # role_permission, _ = RolePermission.objects.get_or_create(role=instance)
    if created:
        RolePermission.objects.create(role=instance)

@receiver(post_delete, sender=Role)
def delete_role_permission(sender, instance, **kwargs):
    RolePermission.objects.filter(role=instance).delete()