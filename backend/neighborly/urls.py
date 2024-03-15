from django.urls import path
from django.contrib import admin
from rest_framework import routers
from api import views as api_views

router = routers.DefaultRouter()

urlpatterns = router.urls

urlpatterns += [
    path('admin/', admin.site.urls),
    path('register/', api_views.UserRegistrationView.as_view()),

]