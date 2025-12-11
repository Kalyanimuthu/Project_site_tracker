from django import forms
from .models import CivilTeam, Site

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ["site_name"]

# REMOVE THIS IF NOT NEEDED:
# class CivilTeamForm(forms.ModelForm):
#     class Meta:
#         model = CivilTeam
#         fields = ["mason_count", "helper_count", "payment"]

# NEW UPDATED FORM (OPTIONAL)
class CivilTeamForm(forms.ModelForm):
    class Meta:
        model = CivilTeam
        fields = ["mason_payment", "helper_payment"]
