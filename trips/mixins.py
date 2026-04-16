from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Trip, TripMembership


class TripAccessMixin:
    """
    Mixin para vistas que necesitan acceso a un viaje.
    Comprueba que el usuario es miembro (owner, invitado).
    Inyecta self.trip y self.membership en la vista.
    """

    def dispatch(self, request, *args, **kwargs):
        self.trip = get_object_or_404(Trip, pk=kwargs['trip_pk'])
        # El owner siempre tiene acceso
        if self.trip.owner == request.user:
            self.membership = None
            return super().dispatch(request, *args, **kwargs)
        # Buscar membresía aceptada
        try:
            self.membership = TripMembership.objects.get(
                trip=self.trip,
                user=request.user,
                status='accepted',
            )
        except TripMembership.DoesNotExist:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_user_role(self):
        if self.trip.owner == self.request.user:
            return 'owner'
        return self.membership.role if self.membership else None


class TripEditorMixin(TripAccessMixin):
    """Solo owner e invitado pueden modificar."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        role = self.get_user_role()
        if role not in ('owner', 'invitado'):
            raise PermissionDenied
        return response
