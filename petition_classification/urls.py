# vk_comments_service/urls.py  
from django.contrib import admin  
from django.urls import path  
from django.contrib.auth import views as auth_views
from comments.views import comment_list, add_comment, edit_comment, register_view, login_view, comment_statistics

urlpatterns = [
    path('', comment_list, name='comment_list'),
    path('add/', add_comment, name='add_comment'),
    path('edit/<int:pk>/', edit_comment, name='edit_comment'),
    path('admin/', admin.site.urls),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('comment_statistics/', comment_statistics, name='comment_statistics'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    #path('fetch/', fetch_vk_comments, name='fetch_vk_comments'),

]