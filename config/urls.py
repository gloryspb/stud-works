from django.contrib import admin
from django.urls import include, path

from works.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", HomeView.as_view(), name="home"),
    path("", include("accounts.urls")),
    path("", include("works.urls")),
]

handler403 = "works.views.permission_denied_view"
handler404 = "works.views.page_not_found_view"
