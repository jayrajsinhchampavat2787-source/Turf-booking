from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from booking.models import UserProfile, Turf, TimeSlot, Booking
import datetime
from decimal import Decimal
import uuid


class Command(BaseCommand):
    help = 'Seeds initial sample data for TURFX Cricket Turf Booking System'

    def handle(self, *args, **options):
        self.stdout.write("Seeding TURFX database in Microsoft SQL Server...")

        # 1. Create TimeSlots (6:00 AM to 11:00 PM hourly)
        slots = []
        for h in range(6, 23):
            start = datetime.time(h, 0)
            end = datetime.time(h + 1, 0)
            slot, created = TimeSlot.objects.get_or_create(start_time=start, end_time=end)
            slots.append(slot)
        self.stdout.write(f"✓ Initialized {len(slots)} hourly time slots (06:00 AM to 11:00 PM).")

        # 2. Create Admin Account (Separate Admin Credentials)
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@turfx.com',
                password='admin123',
                first_name='System',
                last_name='Administrator'
            )
            UserProfile.objects.create(user=admin_user, phone_number='9876543210', city='Ahmedabad')
            self.stdout.write("✓ Created Admin user: admin / admin123")
        else:
            admin_user = User.objects.get(username='admin')

        # 3. Create Normal Player Account
        if not User.objects.filter(username='player').exists():
            player_user = User.objects.create_user(
                username='player',
                email='player@turfx.com',
                password='player123',
                first_name='Rahul',
                last_name='Sharma'
            )
            UserProfile.objects.create(user=player_user, phone_number='9988776655', city='Ahmedabad')
            self.stdout.write("✓ Created Regular Player user: player / player123")
        else:
            player_user = User.objects.get(username='player')

        # 4. Insert the 10 Initial Cricket Turfs
        turfs_data = [
            {
                'name': "Lord's",
                'price': Decimal('50.00'),
                'location': 'Drive-In Road, Ahmedabad',
                'description': "Premier cricket turf inspired by the home of cricket. Features international grade 50mm synthetic grass, 30ft high safety netting, and heavy-duty 800W non-glare LED floodlights for night matches.",
                'image_url': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Power-Play',
                'price': Decimal('35.00'),
                'location': 'Ghodasar, Ahmedabad',
                'description': "High-intensity compact box cricket arena engineered for explosive powerplay batting. Professional bounce matting pitch, clean dugouts, and spectator seating.",
                'image_url': 'https://images.unsplash.com/photo-1589487391730-58f20eb2c308?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Boundary',
                'price': Decimal('75.00'),
                'location': 'SG Highway, Bodakdev',
                'description': "Wide-boundary tournament-standard cricket ground with electronic scoreboard, umpire platform, and premium shockpad underlay for maximum joint safety.",
                'image_url': 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Cricket Central',
                'price': Decimal('45.00'),
                'location': 'Navrangpura, Ahmedabad',
                'description': "Centrally located turf with all-weather playing surface. Ideal for corporate leagues and weekend friendly matches. Equipment rentals available on-site.",
                'image_url': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Skyline',
                'price': Decimal('55.00'),
                'location': 'Gota, Ahmedabad',
                'description': "Open-sky rooftop cricket arena with panoramic skyline views, tournament-grade cricket nets, chilled drinking water, and ample parking space.",
                'image_url': 'https://images.unsplash.com/photo-1518091043644-c1d4457512c6?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Pro-League',
                'price': Decimal('60.00'),
                'location': 'Vastrapur, Ahmedabad',
                'description': "Dedicated arena for competitive box cricket teams. High-grip astro-turf provides realistic spin and bounce for bowlers and batsmen alike.",
                'image_url': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Stadium X',
                'price': Decimal('65.00'),
                'location': 'Sindhu Bhavan Road, Ahmedabad',
                'description': "Stadium-feel multi-deck arena with professional stadium floodlights, live streaming cameras, and comfortable pavilion seating for 50 spectators.",
                'image_url': 'https://images.unsplash.com/photo-1589487391730-58f20eb2c308?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Green Arena',
                'price': Decimal('40.00'),
                'location': 'Naroda, Ahmedabad',
                'description': "Lush green monofilament artificial turf designed for high durability. Economical hourly rates, changing room, and hygienic washroom facilities.",
                'image_url': 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Sixer Zone',
                'price': Decimal('70.00'),
                'location': 'Bopal, Ahmedabad',
                'description': "Extra-high 35-foot ceiling net for big-hitters! Features premium anti-slip turf surface, full cricket kit rental, and post-match refreshment counter.",
                'image_url': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
            {
                'name': 'Pitch Perfect',
                'price': Decimal('50.00'),
                'location': 'Maninagar, Ahmedabad',
                'description': "Consistent true-bounce cricket turf ideal for net practice and fast-paced 6-a-side box matches. Well-maintained lighting and clean facilities.",
                'image_url': 'https://images.unsplash.com/photo-1518091043644-c1d4457512c6?q=80&w=900&auto=format&fit=crop',
                'is_featured': True,
                'is_available': True,
            },
        ]

        created_turfs = []
        for tdata in turfs_data:
            turf, created = Turf.objects.update_or_create(
                name=tdata['name'],
                defaults=tdata
            )
            created_turfs.append(turf)
        self.stdout.write(f"✓ Seeded {len(created_turfs)} official cricket turfs.")

        # 5. Insert Sample Live Bookings for Testing
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        day_after = today + datetime.timedelta(days=2)

        # Booking 1: Pending booking for tomorrow
        slot_1 = slots[12] # 18:00 - 19:00
        turf_1 = created_turfs[0] # Lord's
        if not Booking.objects.filter(turf=turf_1, booking_date=tomorrow, slot=slot_1).exists():
            b1 = Booking.objects.create(
                user=player_user,
                turf=turf_1,
                booking_date=tomorrow,
                slot=slot_1,
                customer_name="Rahul Sharma",
                customer_email="player@turfx.com",
                customer_phone="9988776655",
                total_amount=turf_1.price,
                status='Pending',
                admin_notes='Awaiting admin confirmation'
            )
            self.stdout.write(f"✓ Created sample Pending booking: {b1.booking_id}")

        # Booking 2: Accepted booking for day after tomorrow
        slot_2 = slots[14] # 20:00 - 21:00
        turf_2 = created_turfs[1] # Power-Play
        if not Booking.objects.filter(turf=turf_2, booking_date=day_after, slot=slot_2).exists():
            b2 = Booking.objects.create(
                user=player_user,
                turf=turf_2,
                booking_date=day_after,
                slot=slot_2,
                customer_name="Rahul Sharma",
                customer_email="player@turfx.com",
                customer_phone="9988776655",
                total_amount=turf_2.price,
                status='Accepted',
                admin_notes='Approved by venue admin'
            )
            self.stdout.write(f"✓ Created sample Accepted booking: {b2.booking_id}")

        self.stdout.write(self.style.SUCCESS("✓ TURFX database seeding complete in SQL Server!"))
