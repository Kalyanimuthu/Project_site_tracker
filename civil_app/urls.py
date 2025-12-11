from django.urls import path
from . import views

urlpatterns = [
    path("", views.site_list, name="site_list"),
    path("create/", views.site_create, name="site_create"),

    path("<int:site_id>/", views.site_detail, name="site_detail"),
    path("<int:site_id>/update-sections/", views.update_sections, name="update_sections"),
    path("<int:site_id>/update-civil-team/", views.update_civil_team, name="update_civil_team"),
    path("<int:site_id>/filter-entries/", views.filter_entries, name="filter_entries"),
    path("filter-section/", views.filter_section, name="filter_section"),
    path("<int:site_id>/filter-section/", views.filter_section, name="filter_section"),
    path("all-sites-total/", views.all_sites_total, name="all_sites_total"),
    path("sections/", views.section_filter, name="section_filter"),
    path("reset-data/", views.reset_all_data, name="reset_all_data"),
]
