from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sondage/create/', views.sondage_create, name='sondage_create'),
    path('sondage/<int:sondage_id>/edit/', views.sondage_edit, name='sondage_edit'),
    path('sondage/<int:sondage_id>/delete/', views.sondage_delete, name='sondage_delete'),
    path('sondage/<int:sondage_id>/builder/', views.sondage_builder, name='sondage_builder'),
    path('sondage/<int:sondage_id>/view/', views.sondage_view, name='sondage_view'),
    path('sondage/<int:sondage_id>/submit/', views.sondage_submit, name='sondage_submit'),
    path('sondage/<int:sondage_id>/results/', views.sondage_results, name='sondage_results'),
    path('sondage/<int:sondage_id>/question/add/', views.question_add, name='question_add'),
    path('question/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    path('option/<int:option_id>/delete/', views.option_delete, name='option_delete'),
    path('sondage/<int:sondage_id>/autosave/', views.sondage_autosave, name='sondage_autosave'),
    path('sondage/<int:sondage_id>/question/add/ajax/', views.question_add_ajax, name='question_add_ajax'),
    path('question/<int:question_id>/option/add/', views.option_add_ajax, name='option_add_ajax'),
    path('option/<int:option_id>/delete/ajax/', views.option_delete_ajax, name='option_delete_ajax'),
    path('login/', views.custom_login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
]