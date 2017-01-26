from django import forms


class DialogueForm(forms.Form):
    ROLE_CHOICES = (
        ('owner', 'owner'),
        ('guest', 'guest'),
    )
    product_id = forms.IntegerField(required=True)
    role = forms.ChoiceField(required=False, choices=ROLE_CHOICES)
    rental_order_id = forms.IntegerField(required=False)
    sale_offer_id = forms.IntegerField(required=False)

    def clean(self):
        self.cleaned_data['is_owner'] = self.cleaned_data.get('role') == 'owner'
        if self.cleaned_data['is_owner']:
            rental_order_id = self.cleaned_data.get('rental_order_id')
            sale_offer_id = self.cleaned_data.get('sale_offer_id')
            if not rental_order_id and not sale_offer_id:
                raise forms.ValidationError("When role is owner, the rental_order_id or sale_offer_id should be given.")


class MessageForm(forms.Form):
    receiver = forms.IntegerField()
    dialogue = forms.IntegerField()
    content = forms.CharField(widget=forms.Textarea)
