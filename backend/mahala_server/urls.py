from django.urls import path
from django.contrib import admin
from rest_framework import routers
from api import views as api_views

router = routers.DefaultRouter()

urlpatterns = router.urls

urlpatterns += [
    path('admin/', admin.site.urls),
    path('register/', api_views.UserRegistrationView.as_view()),
    path('login/', api_views.LoginView.as_view()),
    path('logout/', api_views.LogoutView.as_view()),
    path('view-available-items/', api_views.AvailableItemsView.as_view()),
    path('main/', api_views.UserView.as_view()),

]