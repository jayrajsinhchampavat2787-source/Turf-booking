from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, default='Ahmedabad')

    def __str__(self):
        return f"{self.user.username} Profile"


class Turf(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Hourly Price (₹)")
    location = models.CharField(max_length=200)
    description = models.TextField()
    image_url = models.CharField(max_length=500, blank=True, default="/static/assets/img/hero-carousel/Box-Cricket.jpg")
    image = models.ImageField(upload_to='turfs/', blank=True, null=True)
    is_available = models.BooleanField(default=True, verbose_name="Available for Booking")
    is_featured = models.BooleanField(default=True, verbose_name="Featured on Homepage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Turf.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url

    def __str__(self):
        return f"{self.name} - ₹{self.price}/hr ({self.location})"


class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ('start_time', 'end_time')

    @property
    def label(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

    def __str__(self):
        return self.label


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-slot__start_time']

    def clean(self):
        # Prevent duplicate booking on same turf, date, and slot unless Rejected
        if self.status != 'Rejected':
            conflicts = Booking.objects.filter(
                turf=self.turf,
                booking_date=self.booking_date,
                slot=self.slot,
                status__in=['Pending', 'Accepted']
            ).exclude(pk=self.pk)
            if conflicts.exists():
                raise ValidationError(f"Slot {self.slot.label} on {self.booking_date} for {self.turf.name} is already booked!")

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
        if not self.total_amount:
            self.total_amount = self.turf.price
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} | {self.turf.name} | {self.booking_date} ({self.slot.label}) - {self.status}"
