from django.db.models import Sum
from datetime import date
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from .models import (
    Site, SiteSection, CivilTeam, CivilSectionDetail, DailyEntry
)
from .forms import SiteForm


def to_decimal(val):
    try:
        return Decimal(str(val))
    except:
        return Decimal("0")


# --------------------------------------
# AUTO CREATE REQUIRED SECTIONS AND TEAMS
# --------------------------------------
def ensure_site_bootstrap(site):
    required_sections = ["carpenter", "civil", "electrical", "misc", "painting", "plumbing", "tiles"]
    existing = set(site.sections.values_list("section_name", flat=True))

    for s in required_sections:
        if s not in existing:
            SiteSection.objects.create(site=site, section_name=s)

    if site.civil_teams.count() == 0:
        default_teams = ["Trichy Team", "Mahesh Team", "Basker Team", "Kerala Team"]
        for t in default_teams:
            CivilTeam.objects.create(site=site, team_name=t)

    try:
        _ = site.civil_details
    except:
        CivilSectionDetail.objects.create(site=site)


# --------------------------------------
# SITE DETAIL PAGE
# --------------------------------------
def site_detail(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    ensure_site_bootstrap(site)

    sections = list(site.sections.all().order_by("section_name"))
    teams = list(site.civil_teams.all().order_by("team_name"))

    civil_team_total = sum(team.total_payment for team in teams)

    for sec in sections:
        if sec.section_name.lower() == "civil":
            sec.payment = civil_team_total

    section_payment_total = sum(s.payment for s in sections)
    section_labour_total = sum(s.labour_count for s in sections)
    section_material_total = sum(s.material_count for s in sections)

    total_mason_count = sum(t.mason_count for t in teams)
    total_helper_count = sum(t.helper_count for t in teams)
    total_mason_payment = sum(t.mason_payment for t in teams)
    total_helper_payment = sum(t.helper_payment for t in teams)
    civil_total_payment = total_mason_payment + total_helper_payment

    # 🔥 IMPORTANT — needed for dropdown!
    all_sites = Site.objects.all().order_by("site_name")

    return render(request, "sites/site_detail.html", {
        "site": site,
        "sections": sections,
        "civil_teams": teams,
        "civil_team_total": civil_team_total,
        "section_payment_total": section_payment_total,
        "section_labour_total": section_labour_total,
        "section_material_total": section_material_total,
        "total_mason_count": total_mason_count,
        "total_helper_count": total_helper_count,
        "total_mason_payment": total_mason_payment,
        "total_helper_payment": total_helper_payment,
        "civil_total_payment": civil_total_payment,

        # 🔥 required for dropdown
        "all_sites": all_sites
    })

# --------------------------------------
# UPDATE SECTIONS + SAVE DAILY ENTRY
# --------------------------------------
@require_POST
def update_sections(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    today = timezone.now().date()

    for sec in site.sections.all():

        # skip civil section (handled separately)
        if sec.section_name.lower() == "civil":
            continue

        # Get values from form
        labour_count = int(request.POST.get(f"labour_{sec.id}", 0))
        material_pay = float(request.POST.get(f"material_payment_{sec.id}", 0))
        labour_rate = float(request.POST.get(f"labour_rate_{sec.id}", sec.labour_rate))

        # Save raw values
        sec.labour_count = labour_count
        sec.material_payment = material_pay
        sec.labour_rate = labour_rate

        # NEW auto-calculated values
        sec.labour_pay = labour_count * labour_rate
        sec.material_pay = material_pay

        sec.payment = sec.labour_pay + sec.material_pay
        sec.save()

        # Save entry log
        DailyEntry.objects.create(
            site=site,
            entry_date=today,
            section_name=sec.section_name,
            labour_count=labour_count,
            material_count=0,
            payment=sec.payment
        )

    return redirect("site_detail", site.id)


# --------------------------------------
# UPDATE CIVIL TEAM + SAVE DAILY ENTRY
# --------------------------------------
@require_POST
def update_civil_team(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    today = timezone.now().date()

    for team in site.civil_teams.all():

        # Counts
        mason_count = int(request.POST.get(f"mason_count_{team.id}", team.mason_count))
        helper_count = int(request.POST.get(f"helper_count_{team.id}", team.helper_count))

        # Rates
        mason_rate = float(request.POST.get(f"mason_rate_{team.id}", team.mason_rate))
        helper_rate = float(request.POST.get(f"helper_rate_{team.id}", team.helper_rate))

        # Save raw values
        team.mason_count = mason_count
        team.helper_count = helper_count
        team.mason_rate = mason_rate
        team.helper_rate = helper_rate

        # Auto-calc payments
        team.mason_payment = mason_count * mason_rate
        team.helper_payment = helper_count * helper_rate

        team.save()

        # Save log
        DailyEntry.objects.create(
            site=site,
            entry_date=today,
            team_name=team.team_name,
            mason_payment=team.mason_payment,
            helper_payment=team.helper_payment,
            total_payment=team.total_payment
        )

    return redirect("site_detail", site.id)


# --------------------------------------
# FILTER ENTRIES (AJAX)
# --------------------------------------


def site_list(request):
    sites = Site.objects.all()
    return render(request, "sites/site_list.html", {"sites": sites})

def site_create(request):
    if request.method == "POST":
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save()
            return redirect("site_detail", site_id=site.id)
    else:
        form = SiteForm()

    return render(request, "sites/site_create.html", {"form": form})

def filter_entries(request, site_id):
    site = get_object_or_404(Site, id=site_id)

    start = request.GET.get("from_date")
    end = request.GET.get("to_date")

    if not start or not end:
        return JsonResponse({"html": "<p>Please select both dates.</p>"})

    # Get all entries between dates
    all_entries = DailyEntry.objects.filter(
        site=site,
        entry_date__range=[start, end]
    ).order_by("-entry_date")

    # Filter only entries with payment > 0
    entries = [
        e for e in all_entries
        if (e.section_name and e.payment > 0) or (e.team_name and e.total_payment > 0)
    ]

    # Calculate totals only from shown entries
    total_section_payment = sum(e.payment for e in entries if e.section_name)
    total_civil_payment = sum(e.total_payment for e in entries if e.team_name)
    grand_total = total_section_payment + total_civil_payment

    # --------------------------
    # BUILD HTML
    # --------------------------
    html = f"""
    <div class='alert alert-info fw-bold'>
        <b>Total Payment:</b> <span class='text-primary'>₹ {grand_total}</span>
    </div>
    """

    if not entries:
        html += "<p>No entries with payment found for this date range.</p>"
        return JsonResponse({"html": html})

    for e in entries:
        if e.section_name:  # Normal section
            html += f"""
            <div class='border p-2 mb-2 rounded'>
                <b>{e.entry_date}</b><br>
                <b>Section:</b> {e.section_name}<br>
                Payment: ₹ {e.payment}
            </div>
            """

        if e.team_name:  # Civil team
            html += f"""
            <div class='border p-2 mb-2 rounded'>
                <b>{e.entry_date}</b><br>
                <b>Team:</b> {e.team_name}<br>
                Mason: ₹ {e.mason_payment} |
                Helper: ₹ {e.helper_payment} |
                Total: ₹ {e.total_payment}
            </div>
            """

    return JsonResponse({"html": html})


def filter_section(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    section = request.GET.get("section")

    # ----------------------------
    # SPECIAL: CIVIL SECTION
    # ----------------------------
    if section.lower() == "civil":
        teams = CivilTeam.objects.filter(site=site)

        html = "<h5 class='mb-3'>Civil Team Payments</h5>"
        html += "<table class='table table-bordered'>"
        html += """
            <tr class='table-light'>
                <th>Team</th>
                <th>Mason</th>
                <th>Helper</th>
                <th>Total</th>
            </tr>
        """

        for t in teams:
            html += f"""
                <tr>
                    <td>{t.team_name}</td>
                    <td>₹ {t.mason_payment}</td>
                    <td>₹ {t.helper_payment}</td>
                    <td class='fw-bold'>₹ {t.total_payment}</td>
                </tr>
            """

        html += "</table>"

        return JsonResponse({"html": html})

    # ----------------------------
    # NORMAL SECTIONS (NOT CIVIL)
    # ----------------------------
    entries = DailyEntry.objects.filter(
        site=site,
        section_name__iexact=section,
        payment__gt=0   # skip empty entries
    ).order_by("-entry_date")

    html = f"<h5>Entries for {section.title()}</h5>"

    if not entries:
        html += "<p class='text-muted'>No entries found.</p>"
    else:
        html += "<table class='table table-bordered'>"
        html += """
            <tr class='table-light'>
                <th>Date</th>
                <th>Labour</th>
                <th>Material</th>
                <th>Payment</th>
            </tr>
        """
        for e in entries:
            html += f"""
                <tr>
                    <td>{e.entry_date}</td>
                    <td>{e.labour_count}</td>
                    <td>{e.material_count}</td>
                    <td>₹ {e.payment}</td>
                </tr>
            """
        html += "</table>"

    return JsonResponse({"html": html})

from django.db.models import Sum

def all_sites_total(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    sites = Site.objects.all()
    site_data = []
    grand_total = 0

    for site in sites:

        # --- Section totals ---
        sections = site.sections.all()
        section_total = sum(s.payment for s in sections)

        # --- Civil totals ---
        civil_total = sum(t.total_payment for t in site.civil_teams.all())

        # if date filter applied → override totals using DailyEntry
        if from_date and to_date:
            filtered_entries = DailyEntry.objects.filter(
                site=site,
                entry_date__range=[from_date, to_date]
            )

            section_total = filtered_entries.filter(section_name__isnull=False)\
                                            .aggregate(total=Sum("payment"))["total"] or 0

            civil_total = filtered_entries.filter(team_name__isnull=False)\
                                          .aggregate(total=Sum("total_payment"))["total"] or 0

        site_total = (section_total or 0) + (civil_total or 0)
        grand_total += site_total

        if site_total > 0:     # only show sites with valid payment
            site_data.append({
                "site": site,
                "section_total": section_total,
                "civil_total": civil_total,
                "site_total": site_total,
        })


    return render(request, "sites/all_sites_total.html", {
        "site_data": site_data,
        "grand_total": grand_total,
        "from_date": from_date,
        "to_date": to_date,
    })

def section_filter(request):
    # Get unique section names from SiteSection table
    sections = SiteSection.objects.values_list("section_name", flat=True).distinct()

    section_name = request.GET.get("section")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    result = []

    if section_name:
        # NORMAL SECTIONS (non-civil)
        if section_name != "civil":
            queryset = DailyEntry.objects.filter(
                section_name=section_name
            )

            if from_date and to_date:
                queryset = queryset.filter(entry_date__range=[from_date, to_date])

            for entry in queryset:
                if entry.payment > 0:  # skip zero entries
                    result.append({
                        "site": entry.site,
                        "section": entry.section_name,
                        "payment": entry.payment
                    })

        else:
            # CIVIL SECTION (uses team entries)
            queryset = DailyEntry.objects.filter(team_name__isnull=False)

            if from_date and to_date:
                queryset = queryset.filter(entry_date__range=[from_date, to_date])

            for entry in queryset:
                if entry.total_payment > 0:
                    result.append({
                        "site": entry.site,
                        "section": "Civil",
                        "payment": entry.total_payment
                    })

    return render(request, "sites/section_filter.html", {
        "sections": sections,
        "section_name": section_name,
        "from_date": from_date,
        "to_date": to_date,
        "result": result,
    })

def reset_all_data(request):
    # Reset SiteSection values
    for sec in SiteSection.objects.all():
        sec.labour_count = 0
        sec.material_count = 0
        sec.payment = 0
        sec.save()

    # Reset CivilTeam values
    for team in CivilTeam.objects.all():
        team.mason_payment = 0
        team.helper_payment = 0
        team.save()

    # Delete ALL DailyEntry logs
    DailyEntry.objects.all().delete()

    return redirect("site_list")
