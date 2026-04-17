from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import FileResponse, Http404
import os

from .models import Trip, TripMembership, Document, Expense, ItineraryItem, TripDay
from .forms import TripForm, DocumentForm, ExpenseForm


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


@login_required
def trip_create(request):
    form = TripForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        trip = form.save(commit=False)
        trip.owner = request.user
        trip.save()
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
    return render(request, 'trips/trip_detail.html', {
        'trip': trip,
        'role': role,
        'members': members,
    })


@login_required
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    form = TripForm(request.POST or None, instance=trip)
    if request.method == 'POST' and form.is_valid():
        form.save()
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
    from .models import Document
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

@login_required
def expenses_global(request):
    """Página global de gastos: muestra todos los gastos del usuario agrupados por viaje."""
    owned = Trip.objects.filter(owner=request.user)
    shared = Trip.objects.filter(
        memberships__user=request.user, memberships__status='accepted'
    ).exclude(owner=request.user)
    user_trips = (owned | shared).distinct().order_by('-start_date')

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        trip_pk = request.POST.get('trip_id')
        trip = get_object_or_404(Trip, pk=trip_pk)
        if _check_trip_access(request, trip) and form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.paid_by = request.user
            expense.save()
            messages.success(request, 'Gasto añadido.')
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

    form = ExpenseForm()
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.paid_by = request.user
            expense.save()
            messages.success(request, 'Gasto añadido.')
            return redirect('expense_list', trip_pk=trip.pk)

    return render(request, 'trips/expense_list.html', {
        'trip': trip,
        'expenses': expenses,
        'total': total,
        'form': form,
    })


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

    days = trip.days.prefetch_related('items').order_by('day_index')

    # Crear días automáticamente si no existen
    if not days.exists() and trip.start_date and trip.end_date:
        from datetime import timedelta
        current = trip.start_date
        idx = 1
        while current <= trip.end_date:
            TripDay.objects.get_or_create(trip=trip, date=current, defaults={'day_index': idx})
            current += timedelta(days=1)
            idx += 1
        days = trip.days.prefetch_related('items').order_by('day_index')

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
def itinerary_item_delete(request, trip_pk, item_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    item = get_object_or_404(ItineraryItem, pk=item_pk, day__trip=trip)
    if trip.owner != request.user and not _check_trip_access(request, trip):
        return redirect('trip_list')
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Actividad eliminada.')
    return redirect('itinerary', trip_pk=trip.pk)
