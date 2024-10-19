import json
import os
import importlib.util
import math
import copy
import zipfile
import shutil

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db import transaction
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.db.models import Avg

from .models import Game, Payoff, Player, UploadedAgent

import rlcard


MODEL_IDS = ['butifarra-dqn']

def _get_model_ids_all():
    MODEL_IDS_ALL = copy.deepcopy(MODEL_IDS)
    agents = UploadedAgent.objects.all()
    for agent in agents:
        path = os.path.join(settings.MEDIA_ROOT, agent.f.name)
        name = agent.name
        game = agent.game
        target_path = os.path.join(os.path.abspath(os.path.join(path, os.pardir)), name)
        module_name = 'model'
        entry = 'Model'
        spec = importlib.util.spec_from_file_location(module_name, os.path.join(target_path, module_name+'.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        M = getattr(module, entry)

        class ModelSpec(object):
            def __init__(self):
                self.model_id = name
                self._entry_point = M
                self.target_path = target_path

            def load(self):
                model = self._entry_point(self.target_path)
                return model
        rlcard.models.registration.model_registry.model_specs[name] = ModelSpec()
        MODEL_IDS_ALL[game].append(name)
    return MODEL_IDS_ALL

PAGE_FIELDS = ['elements_every_page', 'page_index']

def _get_page(result, elements_every_page, page_index):
    elements_every_page = int(elements_every_page)
    page_index = int(page_index)
    total_row = len(result)
    total_page = math.ceil(len(result) / float(elements_every_page))
    begin = page_index * elements_every_page
    end = min((page_index+1) * elements_every_page, len(result))
    result = result[begin:end]
    return result, total_page, total_row

def replay(request):
    if request.method == 'GET':
        name = request.GET['name']
        agent0 = request.GET['agent0']
        agent1 = request.GET['agent1']
        agent2 = request.GET['agent2']
        agent3 = request.GET['agent3']
        index = request.GET['index']
        g = Game.objects.get(name=name, agent0=agent0, agent1=agent1, agent2=agent2, agent3=agent3, index=index)
        json_data = g.replay
        return HttpResponse(json.dumps(json.loads(json_data)))

def query_game(request): 
    if request.method == 'GET': # query_game ? agent0={} & elements_every_page={} & page_index={}
        if not PAGE_FIELDS[0] in request.GET or not PAGE_FIELDS[1] in request.GET:
            return HttpResponse(json.dumps({'value': -1, 'info': 'elements_every_page and page_index should be given'}))
        filter_dict = {key: request.GET.get(key) for key in dict(request.GET).keys() if key not in PAGE_FIELDS}
        result = Game.objects.filter(**filter_dict).order_by('index')
        result, total_page, total_row = _get_page(result, request.GET['elements_every_page'], request.GET['page_index'])
        result = serializers.serialize('json', result, fields=('name', 'index', 'agent0', 'agent1', 'win', 'payoff'))
        return HttpResponse(json.dumps({'value': 0, 'data': json.loads(result), 'total_page': total_page, 'total_row': total_row}))

def query_payoff(request):
    if request.method == 'GET':
        filter_dict = {key: request.GET.get(key) for key in dict(request.GET).keys()}
        result = Payoff.objects.filter(**filter_dict)
        result = serializers.serialize('json', result)
        return HttpResponse(result)

def query_agent_payoff(request):
    if request.method == 'GET':
        if not PAGE_FIELDS[0] in request.GET or not PAGE_FIELDS[1] in request.GET:
            return HttpResponse(json.dumps({'value': -1, 'info': 'elements_every_page and page_index should be given'}))
        if not 'name' in request.GET:
            return HttpResponse(json.dumps({'value': -2, 'info': 'name should be given'}))
        result = list(Payoff.objects.filter(name=request.GET['name']).values('agent0').annotate(payoff = Avg('payoff')).order_by('-payoff'))
        result, total_page, total_row = _get_page(result, request.GET['elements_every_page'], request.GET['page_index'])
        return HttpResponse(json.dumps({'value': 0, 'data': result, 'total_page': total_page, 'total_row': total_row}))