from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('documents/', views.documents_global, name='documents_global'),
    path('expenses/', views.expenses_global, name='expenses_global'),
    path('itinerary/', views.itinerary_global, name='itinerary_global'),
    path('', views.trip_list, name='trip_list'),
    path('new/', views.trip_create, name='trip_create'),
    path('<int:pk>/', views.trip_detail, name='trip_detail'),
    path('<int:pk>/edit/', views.trip_edit, name='trip_edit'),
    path('<int:pk>/delete/', views.trip_delete, name='trip_delete'),
    # Documentos
    path('<int:trip_pk>/documents/', views.document_list, name='document_list'),
    path('<int:trip_pk>/documents/<int:doc_pk>/delete/', views.document_delete, name='document_delete'),
    # Gastos
    path('<int:trip_pk>/expenses/', views.expense_list, name='expense_list'),
    path('<int:trip_pk>/expenses/<int:expense_pk>/delete/', views.expense_delete, name='expense_delete'),
    # Itinerario
    path('<int:trip_pk>/itinerary/', views.itinerary, name='itinerary'),
    path('<int:trip_pk>/itinerary/<int:day_pk>/add/', views.itinerary_item_create, name='itinerary_item_create'),
    path('<int:trip_pk>/itinerary/item/<int:item_pk>/delete/', views.itinerary_item_delete, name='itinerary_item_delete'),
    # Reservas
    path('<int:trip_pk>/reservations/', views.reservation_list, name='reservation_list'),
    path('<int:trip_pk>/reservations/<int:reservation_pk>/delete/', views.reservation_delete, name='reservation_delete'),
    # Invitaciones
    path('<int:trip_pk>/invite/', views.trip_invite, name='trip_invite'),
    path('invite/<str:token>/accept/', views.trip_accept_invite, name='trip_accept_invite'),
    path('<int:trip_pk>/members/<int:membership_pk>/remove/', views.trip_remove_member, name='trip_remove_member'),
    # API IA
    path('api/trips/', views.api_user_trips, name='api_user_trips'),
    path('api/ia/<int:trip_pk>/generate/', views.api_ia_generate, name='api_ia_generate'),
    path('api/ia/chat/', views.api_ia_chat_general, name='api_ia_chat_general'),
    path('api/ia/<int:trip_pk>/chat/', views.api_ia_chat, name='api_ia_chat'),
    path('api/ia/<int:trip_pk>/add-items/', views.api_ia_add_items, name='api_ia_add_items'),
]
