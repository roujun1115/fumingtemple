from django import forms
from .models import Committee, Andou, Light, Donation

class CommitteeForm(forms.ModelForm):
    class Meta:
        model = Committee
        fields = ['year', 'title', 'name']

class AndouForm(forms.ModelForm):
    class Meta:
        model = Andou
        fields = ['year', 'item', 'name', 'address', 'payment_status']

class LightForm(forms.ModelForm):
    class Meta:
        model = Light
        fields = ['year', 'item', 'name', 'payment_status']

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['year', 'name', 'amount']