from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserManagementViewSet, basename='user-management')
router.register(r'agencies', views.AgencyManagementViewSet, basename='agency-management')
router.register(r'roles', views.RoleViewSet, basename='role')

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints remain the same
    path('login/', views.LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Router for ViewSets
    path('', include(router.urls)),
]
