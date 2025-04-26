from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserManagementViewSet, basename='user-management')

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Router for ViewSets
    path('', include(router.urls)),
]
