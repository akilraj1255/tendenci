from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.http import urlquote
from django.http import HttpResponseRedirect

from tendenci.core.base.http import Http403


class PageSecurityCheck(object):
    """
        a decorator to check page security, and redirect accordingly
    """
    def __init__(self, security_level):
        self.page_security_level = security_level.lower()

    def __call__(self, f):
        def check_security(request, *args, **kwargs):
            
            user_security_level = 'anonymous'
            
            if request.user.is_authenticated():
                if request.user.profile.is_superuser:
                    user_security_level = 'superuser'
                elif request.user.profile.is_staff:
                    user_security_level = 'staff'
                else:
                    user_security_level = 'user'
            
            boo = False        
            if self.page_security_level == 'anonymous':
                boo = True
            elif self.page_security_level == 'user':
                if user_security_level <> 'anonymous':
                    boo = True
            elif self.page_security_level == 'superuser':
                if user_security_level == 'superuser':
                    boo = True
            elif self.page_security_level == 'staff':
                if user_security_level == 'staff':
                    boo = True
                    
            if boo:
                # if request.user.is_authenticated(), log an event here
                return f(request, *args, **kwargs)
            else:
                if request.user.is_authenticated():
                    raise Http403
                else:
                    # redirect to login page
                    redirect_field_name=REDIRECT_FIELD_NAME
                    login_url = settings.LOGIN_URL
                    path = urlquote(request.get_full_path())
                    tup = login_url, redirect_field_name, path
                    
                    return HttpResponseRedirect('%s?%s=%s' % tup)
                    #return f(request, *args, **kwargs)
        return check_security

def admin_required(view_method):
    """
    Checks for admin permissions before
    returning method, else raises 403 exception.
    """
    def decorator(request, *args, **kwargs):
        admin = request.user.profile.is_superuser

        if not admin:
            raise Http403

        return view_method(request, *args, **kwargs)

    return decorator

def superuser_required(view_method):
    """
    Checks for superuser permissions before
    returning method, else raises 403 exception.
    """
    def decorator(request, *args, **kwargs):
        superuser = request.user.profile.is_superuser

        if not superuser:
            raise Http403

        return view_method(request, *args, **kwargs)

    return decorator