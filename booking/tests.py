from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from booking.models import UserProfile, Turf, TimeSlot, Booking
import datetime
from decimal import Decimal


class TURFXSystemTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create slots
        self.slot1 = TimeSlot.objects.create(start_time=datetime.time(6, 0), end_time=datetime.time(7, 0))
        self.slot2 = TimeSlot.objects.create(start_time=datetime.time(7, 0), end_time=datetime.time(8, 0))

        # Create Turf (Lord's - ₹50)
        self.turf = Turf.objects.create(
            name="Lord's",
            price=Decimal('50.00'),
            location="Drive-In Road, Ahmedabad",
            description="Premier cricket turf",
            is_available=True,
            is_featured=True
        )

        # Create Normal User
        self.player = User.objects.create_user(
            username="player",
            email="player@turfx.com",
            password="player123",
            first_name="Rahul",
            last_name="Sharma"
        )
        self.player_profile = UserProfile.objects.create(
            user=self.player,
            phone_number="9988776655",
            city="Ahmedabad"
        )

        # Create Separate Admin User
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@turfx.com",
            password="admin123",
            first_name="System",
            last_name="Administrator"
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            phone_number="9876543210",
            city="Ahmedabad"
        )

    def test_homepage_and_turf_listing(self):
        # Homepage
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TURFX")
        self.assertContains(response, "Lord&#x27;s")

        # Turf listing
        list_response = self.client.get(reverse('turf_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Lord&#x27;s")
        self.assertContains(list_response, "50")

    def test_user_registration_and_login(self):
        # Registration
        reg_resp = self.client.post(reverse('register'), {
            'username': 'newplayer',
            'full_name': 'Hardik Pandya',
            'email': 'hardik@turfx.com',
            'phone_number': '9876501234',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(reg_resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='newplayer').exists())

        # Login
        self.client.logout()
        login_resp = self.client.post(reverse('login'), {
            'username': 'newplayer',
            'password': 'password123'
        })
        self.assertEqual(login_resp.status_code, 302)

    def test_separate_admin_login_and_access_control(self):
        # Normal user cannot access admin dashboard
        self.client.login(username='player', password='player123')
        dash_resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(dash_resp.status_code, 302)  # Redirected to admin_login

        # Admin user login through separate admin login page
        self.client.logout()
        admin_login_resp = self.client.post(reverse('admin_login'), {
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(admin_login_resp.status_code, 302)
        self.assertRedirects(admin_login_resp, reverse('admin_dashboard'))

        # Admin can access admin dashboard
        admin_dash_resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(admin_dash_resp.status_code, 200)
        self.assertContains(admin_dash_resp, "Administrator Dashboard")

    def test_real_booking_workflow(self):
        self.client.login(username='player', password='player123')
        test_date = datetime.date.today() + datetime.timedelta(days=3)

        # 1. Player creates booking
        book_resp = self.client.post(reverse('book_turf', args=[self.turf.slug]), {
            'booking_date': test_date.isoformat(),
            'slot_id': self.slot1.id,
            'customer_name': 'Rahul Sharma',
            'customer_email': 'player@turfx.com',
            'customer_phone': '9988776655'
        })
        self.assertEqual(book_resp.status_code, 302)
        self.assertRedirects(book_resp, reverse('my_bookings'))

        # Verify initial status is Pending
        booking = Booking.objects.get(turf=self.turf, booking_date=test_date, slot=self.slot1)
        self.assertEqual(booking.status, 'Pending')
        self.assertEqual(booking.total_amount, Decimal('50.00'))

        # Check My Bookings displays Pending status
        my_book_resp = self.client.get(reverse('my_bookings'))
        self.assertEqual(my_book_resp.status_code, 200)
        self.assertContains(my_book_resp, booking.booking_id)
        self.assertContains(my_book_resp, "Pending")

        # 2. Duplicate booking prevention on same turf, date, and slot
        with self.assertRaises(Exception):
            Booking.objects.create(
                user=self.player,
                turf=self.turf,
                booking_date=test_date,
                slot=self.slot1,
                customer_name='Duplicate Booker',
                customer_email='dup@turfx.com',
                customer_phone='9999999999',
                total_amount=self.turf.price,
                status='Pending'
            )

        # 3. Admin accepts the booking
        self.client.logout()
        self.client.login(username='admin', password='admin123')
        accept_resp = self.client.get(reverse('admin_accept_booking', args=[booking.booking_id]))
        self.assertEqual(accept_resp.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'Accepted')

        # 4. User visits My Bookings and sees Accepted status
        self.client.logout()
        self.client.login(username='player', password='player123')
        updated_resp = self.client.get(reverse('my_bookings'))
        self.assertContains(updated_resp, "Accepted")

        # 5. Admin rejects the booking
        self.client.logout()
        self.client.login(username='admin', password='admin123')
        reject_resp = self.client.get(reverse('admin_reject_booking', args=[booking.booking_id]))
        self.assertEqual(reject_resp.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'Rejected')

    def test_admin_turf_management(self):
        self.client.login(username='admin', password='admin123')

        # Add turf
        add_resp = self.client.post(reverse('admin_add_turf'), {
            'name': 'Power-Play Arena',
            'price': '35.00',
            'location': 'Ghodasar, Ahmedabad',
            'description': 'High-power box cricket arena',
            'is_available': True,
            'is_featured': True
        })
        self.assertEqual(add_resp.status_code, 302)
        new_turf = Turf.objects.get(name='Power-Play Arena')
        self.assertEqual(new_turf.price, Decimal('35.00'))

        # Edit turf price
        edit_resp = self.client.post(reverse('admin_edit_turf', args=[new_turf.id]), {
            'name': 'Power-Play Arena',
            'price': '40.00',
            'location': 'Ghodasar, Ahmedabad',
            'description': 'High-power box cricket arena updated',
            'is_available': True,
            'is_featured': True
        })
        self.assertEqual(edit_resp.status_code, 302)
        new_turf.refresh_from_db()
        self.assertEqual(new_turf.price, Decimal('40.00'))

        # Delete turf
        del_resp = self.client.post(reverse('admin_delete_turf', args=[new_turf.id]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(Turf.objects.filter(id=new_turf.id).exists())
