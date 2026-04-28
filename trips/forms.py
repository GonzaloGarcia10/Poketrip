from django import forms
from .models import Trip, TripMembership, Document, Expense, Reservation


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'title', 'destination', 'start_date', 'end_date',
            'budget', 'currency', 'travel_style',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('La fecha de fin no puede ser anterior a la de inicio.')
        return cleaned_data


class InviteForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    role = forms.ChoiceField(
        choices=[('invitado', 'Invitado')],
        label='Rol',
    )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'file']


class ExpenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.trip = kwargs.pop('trip', None)
        super().__init__(*args, **kwargs)

    def clean_date(self):
        expense_date = self.cleaned_data.get('date')
        if not self.trip or not expense_date:
            return expense_date

        if expense_date < self.trip.start_date or expense_date > self.trip.end_date:
            raise forms.ValidationError(
                'La fecha del gasto debe estar dentro de las fechas del viaje.'
            )

        return expense_date

    class Meta:
        model = Expense
        fields = ['concept', 'amount', 'category', 'currency', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class ReservationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.trip = kwargs.pop('trip', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('La fecha de fin de la reserva no puede ser anterior a la de inicio.')

        if self.trip:
            for field_name, value in [('start_date', start_date), ('end_date', end_date)]:
                if value and (value < self.trip.start_date or value > self.trip.end_date):
                    raise forms.ValidationError(
                        'Las fechas de la reserva deben estar dentro de las fechas del viaje.'
                    )

        return cleaned_data

    class Meta:
        model = Reservation
        fields = ['reservation_type', 'provider', 'locator', 'start_date', 'end_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
