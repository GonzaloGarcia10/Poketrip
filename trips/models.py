import secrets
from django.db import models
from django.contrib.auth.models import User


class Trip(models.Model):
    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'Dólar'),
        ('GBP', 'Libra esterlina'),
        ('JPY', 'Yen japonés'),
        ('MXN', 'Peso mexicano'),
    ]
    TRAVEL_STYLE_CHOICES = [
        ('adventure', 'Aventura'),
        ('cultural', 'Cultural'),
        ('beach', 'Playa'),
        ('city', 'Ciudad'),
        ('nature', 'Naturaleza'),
        ('other', 'Otro'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_trips')
    members = models.ManyToManyField(User, through='TripMembership', related_name='shared_trips', blank=True)
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='EUR')
    travel_style = models.CharField(max_length=20, choices=TRAVEL_STYLE_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.title} — {self.destination}'


class TripDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    day_index = models.PositiveIntegerField()

    class Meta:
        ordering = ['day_index']
        unique_together = ('trip', 'date')

    def __str__(self):
        return f'Día {self.day_index} — {self.date}'


class ItineraryItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('activity', 'Actividad'),
        ('transport', 'Transporte'),
        ('meal', 'Comida'),
        ('accommodation', 'Alojamiento'),
        ('other', 'Otro'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
    ]

    day = models.ForeignKey(TripDay, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='activity')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    location_text = models.CharField(max_length=200, blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f'{self.title} — {self.day}'


class Reservation(models.Model):
    TYPE_CHOICES = [
        ('flight', 'Vuelo'),
        ('hotel', 'Hotel'),
        ('car', 'Alquiler de coche'),
        ('activity', 'Actividad'),
        ('other', 'Otro'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='reservations')
    reservation_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    provider = models.CharField(max_length=200)
    locator = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f'{self.provider} — {self.trip.title}'


class Document(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=200)
    mime_type = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.name} — {self.trip.title}'


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('transport', 'Transporte'),
        ('accommodation', 'Alojamiento'),
        ('food', 'Comida'),
        ('activities', 'Actividades'),
        ('other', 'Otro'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses')
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    concept = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.concept} — {self.amount} {self.currency}'


class AIGeneration(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='ai_generations')
    parameters = models.JSONField(default=dict)
    prompt = models.TextField()
    response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'IA — {self.trip.title} ({self.created_at.date()})'


class TripMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('editor', 'Editor'),
        ('viewer', 'Visualizador'),
    ]
    STATUS_CHOICES = [
        ('accepted', 'Aceptado'),
        ('pending', 'Pendiente'),
        ('rejected', 'Rechazado'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='memberships')
    invited_email = models.EmailField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='editor')
    token = models.CharField(max_length=64, blank=True)
    expiration = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        identifier = self.user.username if self.user else self.invited_email
        return f'{identifier} — {self.trip.title} ({self.role})'
