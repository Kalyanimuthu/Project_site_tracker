from django.db import models
from decimal import Decimal

class Site(models.Model):
    site_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.site_name


class SiteSection(models.Model):
    site = models.ForeignKey(Site, related_name="sections", on_delete=models.CASCADE)
    section_name = models.CharField(max_length=100)
    labour_count = models.IntegerField(default=0)
    material_count = models.IntegerField(default=0)
    payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.section_name} - {self.site.site_name}"


class CivilTeam(models.Model):
    site = models.ForeignKey(Site, related_name="civil_teams", on_delete=models.CASCADE)
    team_name = models.CharField(max_length=100)
    mason_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    helper_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def total_payment(self):
        return (self.mason_payment or 0) + (self.helper_payment or 0)

    def __str__(self):
        return self.team_name


class CivilSectionDetail(models.Model):
    site = models.OneToOneField(Site, related_name="civil_details", on_delete=models.CASCADE)

    def __str__(self):
        return f"Civil Detail - {self.site.site_name}"


# -------------------------
# NEW MODEL: Daily Entry
# -------------------------
class DailyEntry(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    entry_date = models.DateField()

    # For normal sections
    section_name = models.CharField(max_length=100, blank=True, null=True)
    labour_count = models.IntegerField(default=0)
    material_count = models.IntegerField(default=0)
    payment = models.FloatField(default=0)

    # For civil teams
    team_name = models.CharField(max_length=100, blank=True, null=True)
    mason_payment = models.FloatField(default=0)
    helper_payment = models.FloatField(default=0)
    total_payment = models.FloatField(default=0)

    def __str__(self):
        return f"{self.site} - {self.entry_date}"
