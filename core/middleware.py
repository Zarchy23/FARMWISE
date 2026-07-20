"""
Security and Audit Middleware
Logs user actions for compliance and security monitoring
"""

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from core.models import AuditLog, User


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log user actions for audit trail
    """
    
    def process_request(self, request):
        """Log each request for audit purposes"""
        if request.user.is_authenticated:
            # Only log certain actions to avoid too much noise
            if request.method in ['POST', 'PUT', 'DELETE']:
                self._log_action(request, request.method)
        return None
    
    def _log_action(self, request, action):
        """Create an audit log entry"""
        try:
            # Determine the model being acted upon
            model_name = self._get_model_name(request)
            object_id = self._get_object_id(request)
            
            # Map HTTP methods to audit actions
            action_map = {
                'POST': 'create',
                'PUT': 'update',
                'DELETE': 'delete',
                'GET': 'read'
            }
            
            audit_action = action_map.get(action, 'activity')
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action=audit_action,
                model_name=model_name,
                object_id=object_id,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={
                    'method': request.method,
                    'path': request.path,
                    'query_string': request.GET.urlencode()
                }
            )
        except Exception as e:
            # Don't break the request if logging fails
            pass
    
    def _get_model_name(self, request):
        """Extract model name from request path"""
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2:
            # Try to get model from URL pattern
            return path_parts[1] if path_parts[1] else 'unknown'
        return 'unknown'
    
    def _get_object_id(self, request):
        """Extract object ID from request"""
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[2].isdigit():
            return path_parts[2]
        return ''
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login"""
    AuditLog.objects.create(
        user=user,
        action='login',
        model_name='User',
        object_id=str(user.id),
        ip_address=AuditMiddleware()._get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={'path': request.path}
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    if user:
        AuditLog.objects.create(
            user=user,
            action='logout',
            model_name='User',
            object_id=str(user.id),
            ip_address=AuditMiddleware()._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'path': request.path}
        )


class RateLimitMiddleware(MiddlewareMixin):
    """
    Basic rate limiting middleware
    """
    
    def process_request(self, request):
        """Check rate limits"""
        # This is a placeholder for rate limiting logic
        # Implement actual rate limiting based on your requirements
        return None
