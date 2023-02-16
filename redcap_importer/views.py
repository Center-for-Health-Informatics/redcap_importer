import time

from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

from . import models


def user_can_view_redcap_importer(user):
    """
    Superusers and users belonging to the Django group "view redcap_importer" can see all
    redcap_importer views. This gives full access to any data imported from REDCap!
    """
    if user.groups.filter(name="view redcap_importer").exists() or user.is_superuser:
        return True
    raise PermissionDenied()


@login_required
@user_passes_test(user_can_view_redcap_importer)
def home(request):
    qConnection = models.RedcapConnection.objects.all()
    context = {"qConnection": qConnection}
    return render(request, "redcap_importer/home.html", context)


@login_required
@user_passes_test(user_can_view_redcap_importer)
def project_details_events(request, project_id, data_source="django"):
    oProject = get_object_or_404(models.ProjectMetadata, pk=project_id)
    context = {
        "oProject": oProject,
        "current_tab": "events",
        "data_source": data_source,
    }
    if oProject.count_arms() == 1:
        return render(request, "redcap_importer/project_details_events.html", context)
    return render(request, "redcap_importer/project_details_events_multi_arm.html", context)


@login_required
@user_passes_test(user_can_view_redcap_importer)
def project_details_instruments(request, project_id, data_source="django"):
    oProject = get_object_or_404(models.ProjectMetadata, pk=project_id)
    context = {
        "oProject": oProject,
        "current_tab": "instruments",
        "data_source": data_source,
    }
    return render(request, "redcap_importer/project_details_instruments.html", context)


@login_required
@user_passes_test(user_can_view_redcap_importer)
def project_details_records(request, project_id, data_source="django"):
    oProject = get_object_or_404(models.ProjectMetadata, pk=project_id)
    ProjectRoot = oProject.get_actual_project_root_model()
    qRoot = ProjectRoot.objects.all()
    paginator = Paginator(qRoot, 20)
    page_number = request.GET.get("page", 1)
    context = {
        "oProject": oProject,
        "qRoot": paginator.get_page(page_number),
        "current_tab": "records",
        "data_source": data_source,
    }
    return render(request, "redcap_importer/project_details_records.html", context)


@login_required
@user_passes_test(user_can_view_redcap_importer)
def instrument_details(request, project_id, instrument_id, data_source="django"):
    oProject = get_object_or_404(models.ProjectMetadata, pk=project_id)
    oInstrument = get_object_or_404(models.InstrumentMetadata, pk=instrument_id)
    context = {
        "oProject": oProject,
        "oInstrument": oInstrument,
        "data_source": data_source,
    }
    return render(request, "redcap_importer/instrument_details.html", context)


@login_required
@user_passes_test(user_can_view_redcap_importer)
def field_details(request, project_id, field_id, data_source="django"):
    oProject = get_object_or_404(models.ProjectMetadata, pk=project_id)
    oField = get_object_or_404(models.FieldMetadata, pk=field_id)
    field_values = oField.get_field_values()
    stats, all_counts = oField.get_stats()

    context = {
        "oProject": oProject,
        "oField": oField,
        "field_values": field_values,
        "stats": stats,
        "all_counts": all_counts,
        "data_source": data_source,
    }
    return render(request, "redcap_importer/field_details.html", context)


@login_required
@user_passes_test(user_can_view_redcap_importer)
def redcap_record(request, project_id, record_id, data_source="django"):
    oProject = get_object_or_404(models.ProjectMetadata, pk=project_id)
    ProjectRoot = oProject.get_actual_project_root_model()
    oRoot = ProjectRoot.objects.get(pk=record_id)

    context = {
        "oProject": oProject,
        "oRoot": oRoot,
        "data_source": data_source,
    }
    return render(request, "redcap_importer/redcap_record.html", context)


@login_required
def ajax_recent_upload_list(request):
    # time.sleep(1)       # if this runs too fast, the user can't see that it updated
    context = {}
    context["qLog"] = models.EtlLog.objects.filter(direction=models.EtlLog.Direction.UPLOAD)[:100]
    response = {}
    response["html"] = render_to_string("redcap_importer/snippets/upload_log_list.html", context)
    return JsonResponse(response)
