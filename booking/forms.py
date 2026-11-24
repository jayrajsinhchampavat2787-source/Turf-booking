from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Turf, Booking, TimeSlot


class UserRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose username', 'required': True})
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name', 'required': True})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com', 'required': True})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number', 'required': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create password (min 6 chars)', 'required': True})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password', 'required': True})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email', 'required': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password', 'required': True})
    )


class AdminLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admin Username', 'required': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Admin Password', 'required': True})
    )


class BookingForm(forms.Form):
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True})
    )
    slot_id = forms.IntegerField(widget=forms.HiddenInput())
    customer_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name', 'required': True})
    )
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address', 'required': True})
    )
    customer_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number', 'required': True})
    )


class TurfForm(forms.ModelForm):
    class Meta:
        model = Turf
        fields = ['name', 'price', 'location', 'description', 'image_url', 'image', 'is_available', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Turf Name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1.00', 'placeholder': 'e.g. 50'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Area / Landmark, City'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Turf details and specifications'}),
            'image_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Image URL'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
