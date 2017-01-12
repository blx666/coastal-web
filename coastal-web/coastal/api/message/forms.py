from django import forms


class DialogueForm(forms.Form):
    product_id = forms.IntegerField(required=True)


class MessageForm(forms.Form):
    receiver = forms.IntegerField()
    dialogue = forms.IntegerField()
    content = forms.CharField(widget=forms.Textarea)
