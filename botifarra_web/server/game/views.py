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

import rlcard


MODEL_IDS = ['butifarra-dqn']

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
