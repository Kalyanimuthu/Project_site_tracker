from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Site, SiteSection, CivilTeam, CivilSectionDetail

@receiver(post_save, sender=Site)
def create_default_sections(sender, instance, created, **kwargs):
    if created:

        # Create sections except civil
        sections = ["electrical", "plumbing", "painting", "carpenter", "misc", "tiles"]
        for sec in sections:
            SiteSection.objects.create(site=instance, section_name=sec)

        # Civil main section
        SiteSection.objects.create(site=instance, section_name="civil")

        # Civil special details
        CivilSectionDetail.objects.create(site=instance)

        # Civil teams
        team_names = ["Trichy Team", "Mahesh Team", "Basker Team", "Kerala Team"]
        for name in team_names:
            CivilTeam.objects.create(site=instance, team_name=name)
