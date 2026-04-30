from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
import os
import json

from .models import Trip, TripMembership, Document, Expense, ItineraryItem, TripDay, Reservation
from .forms import TripForm, DocumentForm, ExpenseForm, ReservationForm, InviteForm


@login_required
def dashboard(request):
    owned = Trip.objects.filter(owner=request.user)
    shared = Trip.objects.filter(
        memberships__user=request.user,
        memberships__status='accepted',
    ).exclude(owner=request.user)
    trips = (owned | shared).distinct().order_by('-start_date')[:6]
    return render(request, 'trips/dashboard.html', {'trips': trips})


@login_required
def trip_list(request):
    owned = Trip.objects.filter(owner=request.user)
    shared = Trip.objects.filter(
        memberships__user=request.user,
        memberships__status='accepted',
    ).exclude(owner=request.user)
    trips = (owned | shared).distinct().order_by('-start_date')
    return render(request, 'trips/trip_list.html', {'trips': trips})


def _sync_trip_days(trip):
    if not trip.start_date or not trip.end_date:
        return trip.days.none()

    trip.days.exclude(date__range=(trip.start_date, trip.end_date)).delete()

    current = trip.start_date
    idx = 1
    while current <= trip.end_date:
        day, created = TripDay.objects.get_or_create(
            trip=trip,
            date=current,
            defaults={'day_index': idx},
        )
        if not created and day.day_index != idx:
            day.day_index = idx
            day.save(update_fields=['day_index'])
        current += timedelta(days=1)
        idx += 1

    return trip.days.prefetch_related('items').order_by('day_index')


def _add_form_error_messages(request, form):
    for errors in form.errors.values():
        for error in errors:
            messages.error(request, error)


@login_required
def trip_create(request):
    form = TripForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        trip = form.save(commit=False)
        trip.owner = request.user
        trip.save()
        _sync_trip_days(trip)
        TripMembership.objects.create(
            trip=trip,
            user=request.user,
            role='owner',
            status='accepted',
        )
        messages.success(request, 'Viaje creado correctamente.')
        return redirect('trip_detail', pk=trip.pk)
    return render(request, 'trips/trip_form.html', {'form': form, 'action': 'Crear viaje'})


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    # Solo miembros aceptados o el owner pueden ver
    is_owner = trip.owner == request.user
    is_member = TripMembership.objects.filter(
        trip=trip, user=request.user, status='accepted'
    ).exists()
    if not is_owner and not is_member:
        messages.error(request, 'No tienes acceso a este viaje.')
        return redirect('trip_list')

    role = 'owner' if is_owner else TripMembership.objects.get(
        trip=trip, user=request.user, status='accepted'
    ).role
    members = TripMembership.objects.filter(trip=trip, status='accepted').select_related('user')

    # Mostrar enlace de la ultima invitación creada en este viaje (una sola vez)
    last_invite = None
    pending = request.session.get('last_invite')
    if pending and pending.get('trip_pk') == trip.pk:
        last_invite = pending
        del request.session['last_invite']

    return render(request, 'trips/trip_detail.html', {
        'trip': trip,
        'role': role,
        'members': members,
        'last_invite': last_invite,
    })

@login_required
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    form = TripForm(request.POST or None, instance=trip)
    if request.method == 'POST' and form.is_valid():
        trip = form.save()
        _sync_trip_days(trip)
        messages.success(request, 'Viaje actualizado.')
        return redirect('trip_detail', pk=trip.pk)
    return render(request, 'trips/trip_form.html', {'form': form, 'action': 'Editar viaje', 'trip': trip})


@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    if request.method == 'POST':
        trip.delete()
        messages.success(request, 'Viaje eliminado.')
        return redirect('trip_list')
    return render(request, 'trips/trip_confirm_delete.html', {'trip': trip})


# Documentos

@login_required
def documents_global(request):
    """Página global de documentos: muestra todos los docs del usuario y permite subir."""
    # Viajes accesibles por el usuario
    owned = Trip.objects.filter(owner=request.user)
    shared = Trip.objects.filter(
        memberships__user=request.user, memberships__status='accepted'
    ).exclude(owner=request.user)
    user_trips = (owned | shared).distinct().order_by('-start_date')

    q = request.GET.get('q', '').strip()
    documents = Document.objects.filter(trip__in=user_trips).select_related('trip', 'uploaded_by')
    if q:
        documents = documents.filter(name__icontains=q)

    form = DocumentForm()
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        trip_pk = request.POST.get('trip_id')
        trip = get_object_or_404(Trip, pk=trip_pk)
        if _check_trip_access(request, trip) and form.is_valid():
            doc = form.save(commit=False)
            doc.trip = trip
            doc.uploaded_by = request.user
            ext = os.path.splitext(doc.file.name)[1].lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            }
            doc.mime_type = mime_map.get(ext, 'application/octet-stream')
            doc.save()
            messages.success(request, f'"{doc.name}" subido correctamente.')
            return redirect('documents_global')

    return render(request, 'trips/documents_global.html', {
        'documents': documents,
        'user_trips': user_trips,
        'form': form,
        'q': q,
    })


def _check_trip_access(request, trip):
    is_owner = trip.owner == request.user
    is_member = TripMembership.objects.filter(
        trip=trip, user=request.user, status='accepted'
    ).exists()
    return is_owner or is_member


@login_required
def document_list(request, trip_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    if not _check_trip_access(request, trip):
        messages.error(request, 'No tienes acceso a este viaje.')
        return redirect('trip_list')

    q = request.GET.get('q', '').strip()
    documents = trip.documents.select_related('uploaded_by')
    if q:
        documents = documents.filter(name__icontains=q)

    form = DocumentForm()
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.trip = trip
            doc.uploaded_by = request.user
            # Detectar mime_type por extensión
            ext = os.path.splitext(doc.file.name)[1].lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
            }
            doc.mime_type = mime_map.get(ext, 'application/octet-stream')
            doc.save()
            messages.success(request, f'"{doc.name}" subido correctamente.')
            return redirect('document_list', trip_pk=trip.pk)

    return render(request, 'trips/document_list.html', {
        'trip': trip,
        'documents': documents,
        'form': form,
        'q': q,
    })


@login_required
def document_delete(request, trip_pk, doc_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    doc = get_object_or_404(Document, pk=doc_pk, trip=trip)
    if doc.uploaded_by != request.user and trip.owner != request.user:
        messages.error(request, 'No puedes eliminar este documento.')
        return redirect('document_list', trip_pk=trip.pk)
    if request.method == 'POST':
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Documento eliminado.')
    return redirect('documents_global')


# Gastos

def _get_budget_warning(trip):
    if not trip.budget:
        return None

    total_spent = trip.expenses.aggregate(total=Sum('amount'))['total'] or 0
    if total_spent <= trip.budget:
        return None

    over_budget = total_spent - trip.budget
    return f'Has superado el presupuesto de este viaje por {over_budget:.2f} {trip.currency}.'

@login_required
def expenses_global(request):
    """Página global de gastos: muestra todos los gastos del usuario agrupados por viaje."""
    owned = Trip.objects.filter(owner=request.user)
    shared = Trip.objects.filter(
        memberships__user=request.user, memberships__status='accepted'
    ).exclude(owner=request.user)
    user_trips = (owned | shared).distinct().order_by('-start_date')

    if request.method == 'POST':
        trip_pk = request.POST.get('trip_id')
        trip = get_object_or_404(Trip, pk=trip_pk)
        form = ExpenseForm(request.POST, trip=trip)
        if _check_trip_access(request, trip) and form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.paid_by = request.user
            expense.save()
            messages.success(request, 'Gasto añadido.')
            budget_warning = _get_budget_warning(trip)
            if budget_warning:
                messages.warning(request, budget_warning)
        elif _check_trip_access(request, trip):
            _add_form_error_messages(request, form)
        return redirect('expenses_global')

    q = request.GET.get('q', '').strip()
    expenses = Expense.objects.filter(trip__in=user_trips).select_related('trip', 'paid_by').order_by('-date')
    if q:
        expenses = expenses.filter(Q(concept__icontains=q) | Q(trip__title__icontains=q))

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'trips/expenses_global.html', {
        'expenses': expenses,
        'user_trips': user_trips,
        'total': total,
        'q': q,
    })


@login_required
def expense_list(request, trip_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    if not _check_trip_access(request, trip):
        messages.error(request, 'No tienes acceso a este viaje.')
        return redirect('trip_list')

    expenses = trip.expenses.select_related('paid_by').order_by('-date')
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    form = ExpenseForm(trip=trip)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, trip=trip)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.paid_by = request.user
            expense.save()
            messages.success(request, 'Gasto añadido.')
            budget_warning = _get_budget_warning(trip)
            if budget_warning:
                messages.warning(request, budget_warning)
            return redirect('expense_list', trip_pk=trip.pk)
        _add_form_error_messages(request, form)

    return render(request, 'trips/expense_list.html', {
        'trip': trip,
        'expenses': expenses,
        'total': total,
        'form': form,
    })


@login_required
def expense_edit(request, trip_pk, expense_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    expense = get_object_or_404(Expense, pk=expense_pk, trip=trip)
    if expense.paid_by != request.user and trip.owner != request.user:
        messages.error(request, 'No puedes editar este gasto.')
        return redirect('expense_list', trip_pk=trip.pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, trip=trip)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto actualizado.')
            budget_warning = _get_budget_warning(trip)
            if budget_warning:
                messages.warning(request, budget_warning)
        else:
            _add_form_error_messages(request, form)
    return redirect('expense_list', trip_pk=trip.pk)


@login_required
def expense_delete(request, trip_pk, expense_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    expense = get_object_or_404(Expense, pk=expense_pk, trip=trip)
    if expense.paid_by != request.user and trip.owner != request.user:
        messages.error(request, 'No puedes eliminar este gasto.')
        return redirect('expense_list', trip_pk=trip.pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Gasto eliminado.')
    return redirect('expense_list', trip_pk=trip.pk)


# ── Itinerario ──────────────────────────────────────────────────

@login_required
def itinerary_global(request):
    """Página global de itinerario: lista todos los viajes con sus días e ítems."""
    owned = Trip.objects.filter(owner=request.user)
    shared = Trip.objects.filter(
        memberships__user=request.user, memberships__status='accepted'
    ).exclude(owner=request.user)
    user_trips = (owned | shared).distinct().prefetch_related(
        'days__items'
    ).order_by('-start_date')

    return render(request, 'trips/itinerary_global.html', {
        'user_trips': user_trips,
    })


@login_required
def itinerary(request, trip_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    if not _check_trip_access(request, trip):
        messages.error(request, 'No tienes acceso a este viaje.')
        return redirect('trip_list')

    days = _sync_trip_days(trip)

    return render(request, 'trips/itinerary.html', {
        'trip': trip,
        'days': days,
    })


@login_required
def itinerary_item_create(request, trip_pk, day_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    day = get_object_or_404(TripDay, pk=day_pk, trip=trip)
    if not _check_trip_access(request, trip):
        return redirect('trip_list')

    if request.method == 'POST':
        item_type = request.POST.get('item_type', 'activity')
        title = request.POST.get('title', '').strip()
        start_time = request.POST.get('start_time') or None
        end_time = request.POST.get('end_time') or None
        location = request.POST.get('location_text', '').strip()
        description = request.POST.get('description', '').strip()
        if title:
            ItineraryItem.objects.create(
                day=day,
                item_type=item_type,
                title=title,
                start_time=start_time,
                end_time=end_time,
                location_text=location,
                description=description,
            )
            messages.success(request, 'Actividad añadida.')
    return redirect('itinerary', trip_pk=trip.pk)


@login_required
def itinerary_item_edit(request, trip_pk, item_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    item = get_object_or_404(ItineraryItem, pk=item_pk, day__trip=trip)
    if not _check_trip_access(request, trip):
        return redirect('trip_list')
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        item_type = request.POST.get('item_type', item.item_type)
        start_time = request.POST.get('start_time') or None
        end_time = request.POST.get('end_time') or None
        location = request.POST.get('location_text', '').strip()
        description = request.POST.get('description', '').strip()
        if title:
            item.title = title
            item.item_type = item_type
            item.start_time = start_time
            item.end_time = end_time
            item.location_text = location
            item.description = description
            item.save()
            messages.success(request, 'Actividad actualizada.')
    return redirect('itinerary', trip_pk=trip.pk)


@login_required
def itinerary_item_delete(request, trip_pk, item_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    item = get_object_or_404(ItineraryItem, pk=item_pk, day__trip=trip)
    if trip.owner != request.user and not _check_trip_access(request, trip):
        return redirect('trip_list')
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Actividad eliminada.')
    return redirect('itinerary', trip_pk=trip.pk)


# ── Reservas ──────────────────────────────────────────────

@login_required
def reservation_list(request, trip_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    if not _check_trip_access(request, trip):
        messages.error(request, 'No tienes acceso a este viaje.')
        return redirect('trip_list')

    reservations = trip.reservations.order_by('start_date')
    form = ReservationForm(trip=trip)

    if request.method == 'POST':
        form = ReservationForm(request.POST, trip=trip)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.trip = trip
            reservation.save()
            messages.success(request, 'Reserva añadida.')
            return redirect('reservation_list', trip_pk=trip.pk)
        _add_form_error_messages(request, form)

    return render(request, 'trips/reservation_list.html', {
        'trip': trip,
        'reservations': reservations,
        'form': form,
    })


@login_required
def reservation_delete(request, trip_pk, reservation_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    reservation = get_object_or_404(Reservation, pk=reservation_pk, trip=trip)
    if trip.owner != request.user and not _check_trip_access(request, trip):
        messages.error(request, 'No tienes permiso.')
        return redirect('reservation_list', trip_pk=trip.pk)
    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Reserva eliminada.')
    return redirect('reservation_list', trip_pk=trip.pk)


# ── Invitaciones de miembros ─────────────────────────────────

@login_required
def trip_invite(request, trip_pk):
    trip = get_object_or_404(Trip, pk=trip_pk, owner=request.user)
    if request.method == 'POST':
        form = InviteForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Evitar invitar al owner o a alguien ya invitado
            if email == request.user.email:
                messages.error(request, 'No puedes invitarte a ti mismo.')
            elif TripMembership.objects.filter(trip=trip, invited_email=email).exists():
                messages.warning(request, f'{email} ya ha sido invitado.')
            else:
                from django.utils import timezone
                from datetime import timedelta
                from django.urls import reverse
                membership = TripMembership.objects.create(
                    trip=trip,
                    invited_email=email,
                    role='invitado',
                    status='pending',
                    expiration=timezone.now() + timedelta(days=7),
                )
                accept_url = request.build_absolute_uri(
                    reverse('trip_accept_invite', args=[membership.token])
                )
                request.session['last_invite'] = {
                    'email': email,
                    'url': accept_url,
                    'trip_pk': trip.pk,
                }
                # Enviar email de invitación
                from django.core.mail import send_mail
                from django.conf import settings as django_settings
                send_mail(
                    subject=f'Te han invitado al viaje "{trip.title}" en PokeTrip',
                    message=(
                        f'Hola,\n\n'
                        f'{request.user.username} te ha invitado a unirte al viaje "{trip.title}" en PokeTrip.\n\n'
                        f'Acepta la invitación haciendo clic en el siguiente enlace:\n{accept_url}\n\n'
                        f'Este enlace expirará en 7 días.\n\n'
                        f'— El equipo de PokeTrip'
                    ),
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
                messages.success(request, f'Invitación enviada a {email}.')
    return redirect('trip_detail', pk=trip.pk)


def trip_accept_invite(request, token):
    """Acepta una invitación a un viaje a través del token."""
    from django.utils import timezone
    membership = get_object_or_404(TripMembership, token=token, status='pending')

    if membership.expiration and membership.expiration < timezone.now():
        messages.error(request, 'Esta invitación ha expirado.')
        return redirect('login')

    if not request.user.is_authenticated:
        request.session['pending_invite_token'] = token
        return redirect(f'/accounts/login/?next=/trips/invite/{token}/accept/')

    membership.user = request.user
    membership.status = 'accepted'
    membership.save()
    messages.success(request, f'¡Te has unido a {membership.trip.title}!')
    return redirect('trip_detail', pk=membership.trip.pk)


@login_required
def trip_remove_member(request, trip_pk, membership_pk):
    trip = get_object_or_404(Trip, pk=trip_pk, owner=request.user)
    membership = get_object_or_404(TripMembership, pk=membership_pk, trip=trip)
    if membership.role == 'owner':
        messages.error(request, 'No puedes eliminar al propietario.')
        return redirect('trip_detail', pk=trip.pk)
    if request.method == 'POST':
        membership.delete()
        messages.success(request, 'Miembro eliminado del viaje.')
    return redirect('trip_detail', pk=trip.pk)


# API endpoints para IA

@login_required
def api_user_trips(request):
    """Devuelve los viajes del usuario en JSON para el modal IA."""
    owned = Trip.objects.filter(owner=request.user)
    shared = Trip.objects.filter(
        memberships__user=request.user, memberships__status='accepted'
    ).exclude(owner=request.user)
    trips = (owned | shared).distinct().order_by('-start_date').values('id', 'title', 'destination')
    return JsonResponse({'trips': list(trips)})


@login_required
def api_ia_generate(request, trip_pk):
    """Genera sugerencias de itinerario basadas en el destino y estilo del viaje."""
    trip = get_object_or_404(Trip, pk=trip_pk)
    if not _check_trip_access(request, trip):
        return JsonResponse({'error': 'Sin acceso'}, status=403)

    style = request.GET.get('style', 'cultural')

    # Sugerencias predefinidas por estilo (sin depéndencia de API externa)
    suggestions_map = {
        'cultural': [
            {'title': f'Visita al museo principal de {trip.destination}', 'item_type': 'activity', 'start_time': '10:00'},
            {'title': f'Paseo por el casco histórico de {trip.destination}', 'item_type': 'activity', 'start_time': '15:00'},
            {'title': 'Cena en restaurante local tradicional', 'item_type': 'meal', 'start_time': '20:00'},
            {'title': 'Visita a mercado de artés local', 'item_type': 'activity', 'start_time': '12:00'},
            {'title': 'Tour guiado por monumentos históricos', 'item_type': 'activity', 'start_time': '09:00'},
        ],
        'adventure': [
            {'title': f'Excursión de senderismo en {trip.destination}', 'item_type': 'activity', 'start_time': '08:00'},
            {'title': 'Actividad de deportes de aventura', 'item_type': 'activity', 'start_time': '11:00'},
            {'title': 'Almuerzo en la naturaleza', 'item_type': 'meal', 'start_time': '13:30'},
            {'title': 'Ruta en bicicleta por los alrededores', 'item_type': 'activity', 'start_time': '16:00'},
            {'title': 'Cena y descanso en alojamiento rural', 'item_type': 'meal', 'start_time': '20:00'},
        ],
        'beach': [
            {'title': 'Mañana en la playa', 'item_type': 'activity', 'start_time': '10:00'},
            {'title': 'Alquiler de barco o kayak', 'item_type': 'activity', 'start_time': '12:00'},
            {'title': 'Comida de marisco en chiringuito', 'item_type': 'meal', 'start_time': '14:00'},
            {'title': 'Snorkel o buceo', 'item_type': 'activity', 'start_time': '16:30'},
            {'title': 'Puesta de sol y cena en el paseo maritimo', 'item_type': 'meal', 'start_time': '20:30'},
        ],
        'gastronomy': [
            {'title': 'Desayuno en café local destacado', 'item_type': 'meal', 'start_time': '09:00'},
            {'title': 'Tour gastronómico por el mercado central', 'item_type': 'activity', 'start_time': '11:00'},
            {'title': 'Cata de vinos o cervezas artesanales', 'item_type': 'activity', 'start_time': '13:00'},
            {'title': 'Clase de cocina local', 'item_type': 'activity', 'start_time': '16:00'},
            {'title': 'Cena en restaurante con estrella Michelin o destacado', 'item_type': 'meal', 'start_time': '21:00'},
        ],
        'city': [
            {'title': f'Tour en autobús turístico por {trip.destination}', 'item_type': 'activity', 'start_time': '10:00'},
            {'title': 'Visita a zona de compras y tiendas locales', 'item_type': 'activity', 'start_time': '13:00'},
            {'title': 'Almuerzo en food court o mercado gourmet', 'item_type': 'meal', 'start_time': '14:30'},
            {'title': 'Visita a barrio de moda o arte callejero', 'item_type': 'activity', 'start_time': '17:00'},
            {'title': 'Cena y ambiente nocturno', 'item_type': 'meal', 'start_time': '21:00'},
        ],
    }

    suggestions = suggestions_map.get(style, suggestions_map['cultural'])
    return JsonResponse({'suggestions': suggestions, 'trip': {'id': trip.pk, 'title': trip.title}})


@login_required
def api_ia_chat(request, trip_pk):
    """Chatbot IA: recibe un mensaje y devuelve respuesta de OpenAI."""
    from django.conf import settings as django_settings
    import re as _re

    trip = get_object_or_404(Trip, pk=trip_pk)
    if not _check_trip_access(request, trip):
        return JsonResponse({'error': 'Sin acceso'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    message = data.get('message', '').strip()
    history = data.get('history', [])
    image_base64 = data.get('image_base64', '')
    image_mime = data.get('image_mime', 'image/jpeg')
    if not message and not image_base64:
        return JsonResponse({'error': 'Mensaje vacío'}, status=400)
    if not message:
        message = 'Describe lo que ves en esta imagen.'

    api_key = getattr(django_settings, 'OPENAI_API_KEY', '')
    if not api_key or api_key.startswith('sk-pon'):
        return JsonResponse({'error': 'API key de OpenAI no configurada. Añade tu clave en .env'}, status=503)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        total_days = (trip.end_date - trip.start_date).days + 1 if trip.start_date and trip.end_date else 7
        system_prompt = f"""Eres un asistente de viajes para PokeTrip, una app de planificación de viajes.
El usuario planifica un viaje a {trip.destination} del {trip.start_date} al {trip.end_date} ({total_days} días).
Estilo: {trip.travel_style or 'no especificado'}. Responde siempre en español, de forma amigable y breve.

Cuando el usuario pida un itinerario o actividades concretas, incluye AL FINAL de tu respuesta (sin texto después) este bloque JSON:
```json
[{{"day": 1, "title": "Nombre", "item_type": "activity", "start_time": "10:00", "location_text": "Lugar"}}]
```
Tipos válidos: activity, transport, meal, accommodation, other.
Para preguntas generales responde solo en texto sin JSON."""

        messages_list = [{"role": "system", "content": system_prompt}]
        for h in history[-8:]:
            if h.get('role') in ('user', 'assistant') and h.get('content'):
                messages_list.append({"role": h['role'], "content": h['content']})
        if image_base64:
            user_content = [
                {"type": "text", "text": message},
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_base64}"}},
            ]
        else:
            user_content = message
        messages_list.append({"role": "user", "content": user_content})

        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages_list,
            max_tokens=1200,
            temperature=0.7,
        )
        reply = response.choices[0].message.content

        items = []
        json_match = _re.search(r'```json\s*(\[.*?\])\s*```', reply, _re.DOTALL)
        if json_match:
            try:
                items = json.loads(json_match.group(1))
                reply = reply[:json_match.start()].strip()
            except Exception:
                pass

        return JsonResponse({'reply': reply, 'items': items})

    except Exception as e:
        return JsonResponse({'error': f'Error OpenAI: {str(e)}'}, status=500)

@login_required
def api_ia_chat_general(request):
    """Chatbot IA general: sin viaje específico, conversación libre."""
    from django.conf import settings as django_settings
    import re as _re

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    message = data.get('message', '').strip()
    history = data.get('history', [])
    image_base64 = data.get('image_base64', '')
    image_mime = data.get('image_mime', 'image/jpeg')
    if not message and not image_base64:
        return JsonResponse({'error': 'Mensaje vacío'}, status=400)
    if not message:
        message = 'Describe lo que ves en esta imagen.'

    api_key = getattr(django_settings, 'OPENAI_API_KEY', '')
    if not api_key or api_key.startswith('sk-pon'):
        return JsonResponse({'error': 'API key de OpenAI no configurada.'}, status=503)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        system_prompt = """Eres un asistente de viajes para PokeTrip, una app de planificación de viajes.
Responde siempre en español, de forma amigable y útil.
Puedes ayudar con destinos, consejos de viaje, actividades, gastronomía, presupuestos y cualquier pregunta relacionada con viajes."""

        messages_list = [{"role": "system", "content": system_prompt}]
        for h in history[-8:]:
            if h.get('role') in ('user', 'assistant') and h.get('content'):
                messages_list.append({"role": h['role'], "content": h['content']})
        if image_base64:
            user_content = [
                {"type": "text", "text": message},
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_base64}"}},
            ]
        else:
            user_content = message
        messages_list.append({"role": "user", "content": user_content})

        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages_list,
            max_tokens=1000,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return JsonResponse({'reply': reply, 'items': []})

    except Exception as e:
        return JsonResponse({'error': f'Error OpenAI: {str(e)}'}, status=500)


@login_required
def api_ia_add_items(request, trip_pk):
    """Añade items de itinerario generados por IA al viaje."""
    trip = get_object_or_404(Trip, pk=trip_pk)
    if not _check_trip_access(request, trip):
        return JsonResponse({'error': 'Sin acceso'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    items = data.get('items', [])

    _sync_trip_days(trip)

    added = 0
    for item_data in items:
        day_index = item_data.get('day', 1)
        day = trip.days.filter(day_index=day_index).first() or trip.days.order_by('day_index').first()
        if day:
            ItineraryItem.objects.create(
                day=day,
                title=item_data.get('title', 'Actividad'),
                item_type=item_data.get('item_type', 'activity'),
                start_time=item_data.get('start_time') or None,
                location_text=item_data.get('location_text', ''),
            )
            added += 1

    return JsonResponse({'added': added, 'itinerary_url': f'/trips/{trip_pk}/itinerary/'})
