from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S','Stripe'),
    ('P','PayPal')
)

class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'1234 main st',
        'class':'form-control',
        'id':'address',
    }))

    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder':'Apartment or suite',
        'class':'form-control',
        'id':'address-2',
    }))

    country = CountryField(blank_label='(select country)').formfield( 
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        })
    )

    zip = forms.CharField(widget=forms.TextInput(attrs={
        'class':'form-control',
        'id':'zip',
    }))

    some_shoping_address = forms.BooleanField(required=False)

    save_info = forms.BooleanField(required=False)
    
    payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICES)