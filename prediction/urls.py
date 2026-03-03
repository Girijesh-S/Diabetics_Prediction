"""
URL configuration for prediction app.
"""
from django.urls import path

from . import views

app_name = 'prediction'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('predict/', views.predict_view, name='predict'),
    path('predict/ajax/', views.predict_ajax, name='predict_ajax'),
    path('history/', views.history_view, name='history'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('survey/', views.survey_view, name='survey'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/users/', views.admin_users_view, name='admin_users'),
    path('admin-dashboard/users/<str:username>/', views.admin_user_history_view, name='admin_user_history'),
    path('admin-dashboard/users/<str:username>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('report/<int:pk>/pdf/', views.pdf_report, name='pdf_report'),
    path('train-model/', views.train_model_info, name='train_model'),
    path('set-language/', views.set_language, name='set_language'),
    path('health/', views.health_check, name='health_check'),
]
