

from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from . import models


@login_required
def home(request):
    qConnection = models.RedcapConnection.objects.all()
    context = {
        'qConnection' : qConnection
    }
    return render(request, 'redcap_import/home.html', context)



@login_required
def project_details_events(request, project_id, data_source='django'):
    oProject = get_object_or_404(models.RedcapProject, pk=project_id)
    context = {
        'oProject' : oProject,
        'current_tab' : 'events',
        'data_source' : data_source,
    }
    if oProject.count_arms() == 1:
        return render(request, 'redcap_import/project_details_events.html', context)
    return render(request, 'redcap_import/project_details_events_multi_arm.html', context)

@login_required
def project_details_instruments(request, project_id, data_source='django'):
    oProject = get_object_or_404(models.RedcapProject, pk=project_id)
    context = {
        'oProject' : oProject,
        'current_tab' : 'instruments',
        'data_source' : data_source,
    }
    return render(request, 'redcap_import/project_details_instruments.html', context)

@login_required
def project_details_records(request, project_id, data_source='django'):
    oProject = get_object_or_404(models.RedcapProject, pk=project_id)
    ProjectRoot = oProject.get_actual_project_root_model()
    qRoot = ProjectRoot.objects.all()
    paginator = Paginator(qRoot, 20)
    page_number = request.GET.get('page', 1)
    context = {
        'oProject' : oProject,
        'qRoot' : paginator.get_page(page_number),
        'current_tab' : 'records',
        'data_source' : data_source,
    }
    return render(request, 'redcap_import/project_details_records.html', context)




@login_required
def instrument_details(request, project_id, instrument_id, data_source='django'):
    oProject = get_object_or_404(models.RedcapProject, pk=project_id)
    oInstrument = get_object_or_404(models.Instrument, pk=instrument_id)
    context = {
        'oProject' : oProject,
        'oInstrument' : oInstrument,
        'data_source' : data_source,
    }
    return render(request, 'redcap_import/instrument_details.html', context)

@login_required
def field_details(request, project_id, field_id, data_source='django'):
    oProject = get_object_or_404(models.RedcapProject, pk=project_id)
    oField = get_object_or_404(models.Field, pk=field_id)
    field_values = oField.get_field_values()
    stats, all_counts = oField.get_stats()
        
    context = {
        'oProject' : oProject,
        'oField' : oField,
        'field_values' : field_values,
        'stats' : stats,
        'all_counts' : all_counts,
        'data_source' : data_source,
    }
    return render(request, 'redcap_import/field_details.html', context)

@login_required
def redcap_record(request, project_id, record_id, data_source='django'):
    oProject = get_object_or_404(models.RedcapProject, pk=project_id)
    ProjectRoot = oProject.get_actual_project_root_model()
    oRoot = ProjectRoot.objects.get(pk=record_id)
    
    context = {
        'oProject' : oProject,
        'oRoot' : oRoot,
        'data_source' : data_source,
    }
    return render(request, 'redcap_import/redcap_record.html', context)
    
    
    
    
    
    