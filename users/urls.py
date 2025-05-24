from django.urls import path
from users import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('create-admin/', views.create_admin, name='create_admin'),
] 