from django.urls import path
from . import views

urlpatterns = [
    # User Website
    path('', views.home, name='home'),
    path('turfs/', views.turf_list, name='turf_list'),
    path('turf/<slug:slug>/', views.turf_detail, name='turf_detail'),
    path('book/<slug:slug>/', views.book_turf, name='book_turf'),
    path('api/check-slots/', views.check_slots_api, name='check_slots_api'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('profile/', views.profile_view, name='profile'),

    # User Authentication
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Separate Admin Login & Dashboard
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin-dashboard/booking/<str:booking_id>/accept/', views.admin_accept_booking, name='admin_accept_booking'),
    path('admin-dashboard/booking/<str:booking_id>/reject/', views.admin_reject_booking, name='admin_reject_booking'),
    path('admin-dashboard/turfs/', views.admin_turfs, name='admin_turfs'),
    path('admin-dashboard/turf/add/', views.admin_add_turf, name='admin_add_turf'),
    path('admin-dashboard/turf/<int:id>/edit/', views.admin_edit_turf, name='admin_edit_turf'),
    path('admin-dashboard/turf/<int:id>/delete/', views.admin_delete_turf, name='admin_delete_turf'),
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
]
