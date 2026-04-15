from django.contrib import admin
from .models import Trip, TripDay, ItineraryItem, Reservation, Document, Expense, AIGeneration, TripMembership


class TripDayInline(admin.TabularInline):
    model = TripDay
    extra = 0


class TripMembershipInline(admin.TabularInline):
    model = TripMembership
    extra = 0


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('title', 'destination', 'owner', 'start_date', 'end_date', 'travel_style', 'created_at')
    list_filter = ('travel_style', 'currency')
    search_fields = ('title', 'destination', 'owner__username')
    inlines = [TripDayInline, TripMembershipInline]


@admin.register(TripDay)
class TripDayAdmin(admin.ModelAdmin):
    list_display = ('trip', 'date', 'day_index')
    list_filter = ('trip',)


@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'day', 'item_type', 'start_time', 'end_time', 'status')
    list_filter = ('item_type', 'status')
    search_fields = ('title', 'location_text')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'trip', 'reservation_type', 'locator', 'start_date', 'end_date')
    list_filter = ('reservation_type',)
    search_fields = ('provider', 'locator')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'trip', 'uploaded_by', 'mime_type', 'uploaded_at')
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('concept', 'trip', 'paid_by', 'amount', 'currency', 'category', 'date')
    list_filter = ('category', 'currency')
    search_fields = ('concept',)


@admin.register(AIGeneration)
class AIGenerationAdmin(admin.ModelAdmin):
    list_display = ('trip', 'created_at')
    readonly_fields = ('parameters', 'prompt', 'response', 'created_at')


@admin.register(TripMembership)
class TripMembershipAdmin(admin.ModelAdmin):
    list_display = ('trip', 'user', 'invited_email', 'role', 'status', 'created_at')
    list_filter = ('role', 'status')
