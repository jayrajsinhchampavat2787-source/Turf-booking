from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Q
import datetime
import uuid

from .models import UserProfile, Turf, TimeSlot, Booking
from .forms import (
    UserRegistrationForm, UserLoginForm, AdminLoginForm,
    BookingForm, TurfForm, UserProfileUpdateForm
)


# Helper check for admin/staff
def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def get_default_slots():
    """Ensure standard 1-hour slots from 06:00 AM to 11:00 PM exist in SQL Server."""
    slots = []
    for h in range(6, 23):
        start = datetime.time(h, 0)
        end = datetime.time(h + 1, 0)
        slot, _ = TimeSlot.objects.get_or_create(start_time=start, end_time=end)
        slots.append(slot)
    return slots


# ==============================================================
# USER WEBSITE VIEWS
# ==============================================================

def home(request):
    """TURFX Homepage with banner, logo, quick search, and featured cricket turfs."""
    turfs = Turf.objects.filter(is_available=True)[:6]
    total_turfs = Turf.objects.filter(is_available=True).count()
    context = {
        'featured_turfs': turfs,
        'total_turfs': total_turfs,
    }
    return render(request, 'home.html', context)


def turf_list(request):
    """Explore Turfs listing showing all 10+ cricket turfs with images, prices, locations."""
    turfs = Turf.objects.all()
    q = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'price_asc')

    if q:
        turfs = turfs.filter(Q(name__icontains=q) | Q(location__icontains=q) | Q(description__icontains=q))

    if sort_by == 'price_asc':
        turfs = turfs.order_by('price')
    elif sort_by == 'price_desc':
        turfs = turfs.order_by('-price')
    else:
        turfs = turfs.order_by('name')

    context = {
        'turfs': turfs,
        'q': q,
        'sort_by': sort_by,
        'total_count': turfs.count(),
    }
    return render(request, 'turf_list.html', context)


def turf_detail(request, slug):
    """Turf Details page with specifications and interactive Date & Time Slot Picker."""
    turf = get_object_or_404(Turf, slug=slug)
    all_slots = get_default_slots()

    # Default date: today
    selected_date_str = request.GET.get('date', datetime.date.today().isoformat())
    try:
        selected_date = datetime.date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = datetime.date.today()

    # Query already booked slots for this turf and date (exclude Rejected)
    booked_slot_ids = list(Booking.objects.filter(
        turf=turf,
        booking_date=selected_date,
        status__in=['Pending', 'Accepted']
    ).values_list('slot_id', flat=True))

    context = {
        'turf': turf,
        'all_slots': all_slots,
        'selected_date': selected_date,
        'booked_slot_ids': booked_slot_ids,
        'today': datetime.date.today().isoformat(),
    }
    return render(request, 'turf_detail.html', context)


def check_slots_api(request):
    """AJAX endpoint for real-time slot availability checking."""
    turf_id = request.GET.get('turf_id')
    date_str = request.GET.get('date')

    if not turf_id or not date_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        selected_date = datetime.date.fromisoformat(date_str)
        turf = get_object_or_404(Turf, id=turf_id)
        booked_slot_ids = list(Booking.objects.filter(
            turf=turf,
            booking_date=selected_date,
            status__in=['Pending', 'Accepted']
        ).values_list('slot_id', flat=True))

        return JsonResponse({
            'date': date_str,
            'booked_slot_ids': booked_slot_ids,
            'total_booked': len(booked_slot_ids)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==============================================================
# BOOKING CREATION & CONFIRMATION
# ==============================================================

@login_required
def book_turf(request, slug):
    """Booking page where user confirms match details and saves booking to SQL Server."""
    turf = get_object_or_404(Turf, slug=slug, is_available=True)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking_date = form.cleaned_data['booking_date']
            slot_id = form.cleaned_data['slot_id']
            cust_name = form.cleaned_data['customer_name']
            cust_email = form.cleaned_data['customer_email']
            cust_phone = form.cleaned_data['customer_phone']

            slot = get_object_or_404(TimeSlot, id=slot_id)

            if booking_date < datetime.date.today():
                messages.error(request, "Cannot book for a past date.")
                return redirect('turf_detail', slug=turf.slug)

            # Prevent duplicate bookings using atomic transaction and row locks
            with transaction.atomic():
                conflict = Booking.objects.select_for_update().filter(
                    turf=turf,
                    booking_date=booking_date,
                    slot=slot,
                    status__in=['Pending', 'Accepted']
                ).exists()

                if conflict:
                    messages.error(request, f"Slot {slot.label} on {booking_date} is already booked. Please choose another time.")
                    return redirect('turf_detail', slug=turf.slug)

                booking = Booking.objects.create(
                    user=request.user,
                    turf=turf,
                    booking_date=booking_date,
                    slot=slot,
                    customer_name=cust_name,
                    customer_email=cust_email,
                    customer_phone=cust_phone,
                    total_amount=turf.price,
                    status='Pending',  # Requirement: initial status is Pending
                    admin_notes='Awaiting admin confirmation'
                )

            messages.success(request, f"🎉 Booking created successfully! Reference: #{booking.booking_id}. Status: Pending.")
            return redirect('my_bookings')
        else:
            messages.error(request, "Please fill in all required booking fields correctly.")
    else:
        date_str = request.GET.get('date', datetime.date.today().isoformat())
        slot_id = request.GET.get('slot_id')

        if not slot_id:
            messages.warning(request, "Please select an available time slot first.")
            return redirect('turf_detail', slug=turf.slug)

        slot = get_object_or_404(TimeSlot, id=slot_id)
        try:
            booking_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            booking_date = datetime.date.today()

        # Check if already booked
        if Booking.objects.filter(turf=turf, booking_date=booking_date, slot=slot, status__in=['Pending', 'Accepted']).exists():
            messages.error(request, f"Slot {slot.label} on {booking_date} is already booked.")
            return redirect('turf_detail', slug=turf.slug)

        initial_data = {
            'booking_date': booking_date,
            'slot_id': slot.id,
            'customer_name': request.user.get_full_name() or request.user.username,
            'customer_email': request.user.email,
            'customer_phone': getattr(getattr(request.user, 'profile', None), 'phone_number', ''),
        }
        form = BookingForm(initial=initial_data)

    context = {
        'turf': turf,
        'slot': slot,
        'booking_date': booking_date,
        'form': form,
    }
    return render(request, 'booking_page.html', context)


@login_required
def my_bookings(request):
    """User's previous bookings list displaying status: Pending, Accepted, Rejected."""
    bookings = Booking.objects.filter(user=request.user).select_related('turf', 'slot').order_by('-created_at')
    context = {
        'bookings': bookings,
    }
    return render(request, 'my_bookings.html', context)


@login_required
def profile_view(request):
    """User Profile management."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        city = request.POST.get('city', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()

        profile.phone_number = phone
        profile.city = city
        profile.save()

        messages.success(request, "Your profile has been updated successfully!")
        return redirect('profile')

    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'profile.html', context)


# ==============================================================
# USER REGISTRATION & AUTHENTICATION
# ==============================================================

def register_view(request):
    """Real User Registration."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']
            phone = form.cleaned_data['phone_number']

            name_parts = full_name.split(None, 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            UserProfile.objects.create(user=user, phone_number=phone)

            # Log the new user in immediately
            login(request, user)
            messages.success(request, f"Welcome to TURFX, {first_name}! Your account has been registered.")
            return redirect('home')
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_login_view(request):
    """Real User Login."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login_id = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            # Support both username and email login
            user = authenticate(request, username=login_id, password=password)
            if user is None:
                try:
                    user_obj = User.objects.get(email__iexact=login_id)
                    user = authenticate(request, username=user_obj.username, password=password)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    pass

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next')
                return redirect(next_url if next_url else 'home')
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """User / Admin Logout."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ==============================================================
# SEPARATE ADMIN LOGIN & DASHBOARD
# ==============================================================

def admin_login_view(request):
    """Separate Admin Login Page."""
    if request.user.is_authenticated and is_admin_user(request.user):
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    messages.success(request, f"Welcome to TURFX Admin Panel, {user.username}!")
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "Access denied. Only authorized administrators can access this portal.")
            else:
                messages.error(request, "Invalid administrator credentials.")
    else:
        form = AdminLoginForm()

    return render(request, 'admin_login.html', {'form': form})


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_dashboard(request):
    """Real Admin Dashboard displaying statistics from SQL Server."""
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='Pending').count()
    accepted_bookings = Booking.objects.filter(status='Accepted').count()
    rejected_bookings = Booking.objects.filter(status='Rejected').count()
    total_users = User.objects.filter(is_staff=False).count()
    total_turfs = Turf.objects.count()

    recent_bookings = Booking.objects.select_related('turf', 'user', 'slot').order_by('-created_at')[:10]

    context = {
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'accepted_bookings': accepted_bookings,
        'rejected_bookings': rejected_bookings,
        'total_users': total_users,
        'total_turfs': total_turfs,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'admin_dashboard.html', context)


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_bookings(request):
    """Admin Booking Management Page with Accept and Reject actions."""
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.select_related('turf', 'user', 'slot').order_by('-created_at')

    if status_filter in ['Pending', 'Accepted', 'Rejected']:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'admin_bookings.html', context)


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_accept_booking(request, booking_id):
    """Accept Booking: Updates SQL Server status immediately."""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    booking.status = 'Accepted'
    booking.save()
    messages.success(request, f"✓ Booking #{booking.booking_id} has been ACCEPTED.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_bookings'))


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_reject_booking(request, booking_id):
    """Reject Booking: Updates SQL Server status immediately."""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    booking.status = 'Rejected'
    booking.save()
    messages.warning(request, f"⚠ Booking #{booking.booking_id} has been REJECTED.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_bookings'))


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_turfs(request):
    """Admin Turf Management: view all turfs."""
    turfs = Turf.objects.all().order_by('price')
    return render(request, 'admin_turfs.html', {'turfs': turfs})


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_add_turf(request):
    """Admin Turf Management: Add new turf."""
    if request.method == 'POST':
        form = TurfForm(request.POST, request.FILES)
        if form.is_valid():
            turf = form.save()
            messages.success(request, f"Turf '{turf.name}' has been created successfully!")
            return redirect('admin_turfs')
    else:
        form = TurfForm()
    return render(request, 'admin_turf_form.html', {'form': form, 'title': 'Add New Cricket Turf'})


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_edit_turf(request, id):
    """Admin Turf Management: Edit existing turf price, location, image, availability."""
    turf = get_object_or_404(Turf, id=id)
    if request.method == 'POST':
        form = TurfForm(request.POST, request.FILES, instance=turf)
        if form.is_valid():
            form.save()
            messages.success(request, f"Turf '{turf.name}' details updated successfully!")
            return redirect('admin_turfs')
    else:
        form = TurfForm(instance=turf)
    return render(request, 'admin_turf_form.html', {'form': form, 'turf': turf, 'title': f"Edit {turf.name}"})


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_delete_turf(request, id):
    """Admin Turf Management: Delete turf."""
    turf = get_object_or_404(Turf, id=id)
    if request.method == 'POST':
        name = turf.name
        turf.delete()
        messages.success(request, f"Turf '{name}' was deleted.")
        return redirect('admin_turfs')
    return render(request, 'admin_turf_confirm_delete.html', {'turf': turf})


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_users(request):
    """Admin User Management: View registered users and booking counts."""
    users = User.objects.filter(is_staff=False).annotate(total_bookings=Count('bookings')).order_by('-date_joined')
    return render(request, 'admin_users.html', {'users': users})


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_user_detail(request, user_id):
    """Admin User Management: View user details and complete booking history."""
    target_user = get_object_or_404(User, id=user_id)
    user_bookings = Booking.objects.filter(user=target_user).select_related('turf', 'slot').order_by('-created_at')
    context = {
        'target_user': target_user,
        'user_bookings': user_bookings,
    }
    return render(request, 'admin_user_detail.html', context)
