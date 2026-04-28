from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Expense, Reservation, Trip, TripDay


class ExpenseBudgetWarningTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='gonzalo', password='testpass123')
		self.client.force_login(self.user)
		self.trip = Trip.objects.create(
			owner=self.user,
			title='Lisboa',
			destination='Lisboa',
			start_date='2026-05-10',
			end_date='2026-05-14',
			budget=Decimal('100.00'),
			currency='EUR',
		)

	def test_expense_list_warns_when_budget_is_exceeded(self):
		response = self.client.post(
			reverse('expense_list', kwargs={'trip_pk': self.trip.pk}),
			{
				'concept': 'Hotel',
				'amount': '120.00',
				'category': 'accommodation',
				'currency': 'EUR',
				'date': '2026-05-10',
				'notes': '',
			},
			follow=True,
		)

		self.assertEqual(Expense.objects.count(), 1)
		messages = [str(message) for message in response.context['messages']]
		self.assertIn('Has superado el presupuesto de este viaje por 20.00 EUR.', messages)

	def test_expense_list_does_not_warn_when_budget_is_not_exceeded(self):
		response = self.client.post(
			reverse('expense_list', kwargs={'trip_pk': self.trip.pk}),
			{
				'concept': 'Cena',
				'amount': '40.00',
				'category': 'food',
				'currency': 'EUR',
				'date': '2026-05-10',
				'notes': '',
			},
			follow=True,
		)

		messages = [str(message) for message in response.context['messages']]
		self.assertFalse(any('Has superado el presupuesto de este viaje' in message for message in messages))


class TripDateIntegrityTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='maria', password='testpass123')
		self.client.force_login(self.user)
		self.trip = Trip.objects.create(
			owner=self.user,
			title='Madrid',
			destination='Madrid',
			start_date='2026-04-16',
			end_date='2026-04-18',
			budget=Decimal('300.00'),
			currency='EUR',
		)
		TripDay.objects.create(trip=self.trip, date='2026-04-16', day_index=1)
		TripDay.objects.create(trip=self.trip, date='2026-04-17', day_index=2)
		TripDay.objects.create(trip=self.trip, date='2026-04-18', day_index=3)

	def test_trip_edit_removes_days_outside_new_range(self):
		response = self.client.post(
			reverse('trip_edit', kwargs={'pk': self.trip.pk}),
			{
				'title': 'Madrid',
				'destination': 'Madrid',
				'start_date': '2026-06-13',
				'end_date': '2026-06-14',
				'budget': '300.00',
				'currency': 'EUR',
				'travel_style': 'city',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertQuerySetEqual(
			self.trip.days.order_by('day_index').values_list('date', flat=True),
			[
				'2026-06-13',
				'2026-06-14',
			],
			transform=str,
		)

	def test_expense_list_rejects_expense_outside_trip_dates(self):
		response = self.client.post(
			reverse('expense_list', kwargs={'trip_pk': self.trip.pk}),
			{
				'concept': 'Cena',
				'amount': '40.00',
				'category': 'food',
				'currency': 'EUR',
				'date': '2026-04-25',
				'notes': '',
			},
			follow=True,
		)

		self.assertEqual(Expense.objects.count(), 0)
		messages = [str(message) for message in response.context['messages']]
		self.assertIn('La fecha del gasto debe estar dentro de las fechas del viaje.', messages)

	def test_reservation_list_rejects_reservation_outside_trip_dates(self):
		response = self.client.post(
			reverse('reservation_list', kwargs={'trip_pk': self.trip.pk}),
			{
				'reservation_type': 'hotel',
				'provider': 'Hotel Central',
				'locator': 'ABC123',
				'start_date': '2026-04-20',
				'end_date': '2026-04-21',
				'notes': '',
			},
			follow=True,
		)

		self.assertEqual(Reservation.objects.count(), 0)
		messages = [str(message) for message in response.context['messages']]
		self.assertIn('Las fechas de la reserva deben estar dentro de las fechas del viaje.', messages)
