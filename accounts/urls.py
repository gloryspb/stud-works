from django.urls import path

from .views import RegisterView, RoleAwareLoginView, RoleAwareLogoutView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", RoleAwareLoginView.as_view(), name="login"),
    path("logout/", RoleAwareLogoutView.as_view(), name="logout"),
]
