from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView

from .forms import StudentRegistrationForm, StyledAuthenticationForm
from .models import User


class RegisterView(CreateView):
    model = User
    form_class = StudentRegistrationForm
    template_name = "accounts/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse(request.user.get_post_login_url()))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Role cannot be taken from the request: the form always creates a student.
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Регистрация прошла успешно. Добро пожаловать!")
        return redirect(reverse(user.get_post_login_url()))


class RoleAwareLoginView(LoginView):
    form_class = StyledAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse(self.request.user.get_post_login_url())


class RoleAwareLogoutView(LogoutView):
    http_method_names = ["post", "options"]
