from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('documents/', views.documents_global, name='documents_global'),
    path('', views.trip_list, name='trip_list'),
    path('new/', views.trip_create, name='trip_create'),
    path('<int:pk>/', views.trip_detail, name='trip_detail'),
    path('<int:pk>/edit/', views.trip_edit, name='trip_edit'),
    path('<int:pk>/delete/', views.trip_delete, name='trip_delete'),
    path('<int:trip_pk>/documents/', views.document_list, name='document_list'),
    path('<int:trip_pk>/documents/<int:doc_pk>/delete/', views.document_delete, name='document_delete'),
]
