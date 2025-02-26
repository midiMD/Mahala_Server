from django.urls import path, include
from django.contrib import admin
from django.conf import settings

from rest_framework import routers
from api import views as api_views
from django.conf.urls.static import static

router = routers.DefaultRouter()

urlpatterns = router.urls

urlpatterns += [
    path('admin/', admin.site.urls),
    path('register/', api_views.UserRegistrationView.as_view()),
    path('login/', api_views.LoginView.as_view()),
    path('auth/', api_views.ValidateTokenView.as_view()),
    path('auth/get_user', api_views.GetUserView.as_view()),
    path('logout/', api_views.LogoutView.as_view()),
    path('market/', api_views.MarketView.as_view()),
    path('market/item/', api_views.MarketItemDetailView.as_view()),
    path('main/', api_views.UserView.as_view()),
    path('inventory/upload', api_views.UploadItemView.as_view()),
    path('inventory/items', api_views.InventoryView.as_view()),
    path('inventory/items/detail', api_views.InventoryItemDetailView.as_view()),
    path('inventory/items/delete', api_views.ItemDeleteView.as_view()),
    path('test/test1', api_views.TestView.as_view()),
    path('password-reset/',api_views.PasswordResetView.as_view()),
    path('settings/password-change/',api_views.PasswordChangeView.as_view()),
    #path('chat/', include(chat_routing))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)   # in production, gonna have to serve these from an S3 server or something




