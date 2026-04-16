from django import forms
from .models import Trip, TripMembership, Document


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
        choices=[('editor', 'Editor'), ('viewer', 'Visualizador')],
        label='Rol',
    )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'file']
