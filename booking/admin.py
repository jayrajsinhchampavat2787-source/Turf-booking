from django.contrib import admin
from .models import UserProfile, Turf, TimeSlot, Booking


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city')
    search_fields = ('user__username', 'user__email', 'phone_number')


@admin.register(Turf)
class TurfAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'location', 'is_available', 'is_featured', 'created_at')
    list_filter = ('is_available', 'is_featured')
    search_fields = ('name', 'location', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'is_active')
    list_filter = ('is_active',)
    ordering = ('start_time',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'turf', 'booking_date', 'slot', 'customer_name', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'booking_date', 'turf')
    search_fields = ('booking_id', 'customer_name', 'customer_email', 'customer_phone', 'turf__name')
    readonly_fields = ('booking_id', 'created_at', 'updated_at')
