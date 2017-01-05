from django import forms


class DialogueForm(forms.Form):
    product_id = forms.IntegerField(required=True)