from django import forms
from coastal.apps.review.models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['order', 'score', 'content']

    def clean(self):
        super(ReviewForm,self).clean()
