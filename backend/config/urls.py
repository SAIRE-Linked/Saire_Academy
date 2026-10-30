from django.contrib import admin
from django.urls import include, path
from courses.views import health

admin.site.site_header = "SAIRE-Linked Learning | Administration"
admin.site.site_title = "SAIRE-Linked CMS"
admin.site.index_title = "Courses and curriculum management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health, name="health"),
    path("api/v1/", include("courses.urls")),
]
