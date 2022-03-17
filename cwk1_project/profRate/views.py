from operator import mod
from statistics import StatisticsError, mean
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from profRate.models import Professor, Module, Rating
from django.core import serializers
from django.db import IntegrityError

# Register Account, Must be post, login not required. 
@csrf_exempt
def register(request):
    http_bad_response = HttpResponseBadRequest()
    http_bad_response['Content-Type'] = 'text/plain'

    if request.method == 'POST':
        account = json.loads(request.body.decode('utf-8'))
    else:
        http_bad_response.content = 'Only POST requests are allowed for the register resource\n'
        return http_bad_response

    try:
        user = User.objects.create_user(username=account['username'],
                                        email=account['email'],
                                        password=account['password'])
    except IntegrityError:
        http_bad_response.content = 'User Already Exists\n'
        return http_bad_response
    
    user.save()

    return HttpResponse('OK')

# POST
@csrf_exempt
def login(request):
    http_bad_response = HttpResponseBadRequest()
    http_bad_response['Content-Type'] = 'text/plain'

    if request.method == 'POST':
        account = json.loads(request.body.decode('utf-8'))
    else:
        http_bad_response.content = 'Only POST requests are allowed for the register resource\n'
        return http_bad_response

    user = auth.authenticate(username=account['username'], password=account['password'])
    if user is not None and user.is_active:
        auth.login(request, user)
        return HttpResponse('Logged in')
    else:
        http_bad_response.content = 'Could not log you in'
        return http_bad_response

# GET
def logout(request):
    auth.logout(request)
    return HttpResponse('Logged Out')

# GET
# Lists all modules
def view_modules(request):
    http_bad_response = HttpResponseBadRequest()
    http_bad_response['Content-Type'] = 'text/plain'

    if request.method != 'GET':
        http_bad_response.content = 'Only GET requests are allowed for the register resource\n'
        return http_bad_response
    
    modules = Module.objects.all()
    json_package = []
    for module in modules:
        prof_names = []
        professors = module.professors.all()
        for professor in professors:
            prof_names.append(professor.professor_id + ', ' + professor.name)

        module = module.__dict__
        del module['_state']
        module['professors'] = prof_names
        
        json_package.append(module)
    modules = json.dumps(json_package)

    return HttpResponse(modules, content_type="application/json")

# Given prof id and optional module id calculates average rating and returns number rounded.
def calc_average(prof_id, module_id=None):
    # Check only one professor returned
    if module_id == None:
        prof_search = Professor.objects.get(professor_id = prof_id)

        ratings = prof_search.rating_set.all()
        ratings = ratings.values('rating')

        total = []
        for rating in ratings:
            total.append(int(rating['rating']))

        try: 
            average = round(mean(total))
        except StatisticsError:
            average = 0

        return average
    else:
        modules = Module.objects.all()
        module_ids = []
        for module in modules:
            if module.module_code == module_id:
                module_ids.append(module.id)
        
        total = []
        for id in module_ids:
            prof_search = Rating.objects.filter(professor_reference = prof_id).filter(module_reference = id)

            ratings = list(prof_search.values())

            for rating in ratings:
                total.append(int(rating['rating']))

        try:
            average = round(mean(total))
        except StatisticsError:
            average = 0

        return average

# GET
# list all professors and their overall average rating
def view_professors(request):
    http_bad_response = HttpResponseBadRequest()
    http_bad_response['Content-Type'] = 'text/plain'

    if request.method != 'GET':
        http_bad_response.content = 'Only GET requests are allowed for the register resource\n'
        return http_bad_response
    
    json_package = []
    professors = list(Professor.objects.values())
    for professor in professors:
        json_line = professor
        average = calc_average(prof_id=professor['professor_id'])
        json_line['average'] = average
        json_package.append(json_line)
     
    json_package = json.dumps(json_package)

    return HttpResponse(json_package, content_type="application/json")

# POST
# Takes in prof_id and module_id to calculate average for professor in that module (can be over multiple module instances just same module code)
@csrf_exempt
def average_professor(request):
    http_bad_response = HttpResponseBadRequest()
    http_bad_response['Content-Type'] = 'text/plain'

    if request.method == 'POST':
        package = json.loads(request.body.decode('utf-8'))
    else:
        http_bad_response.content = 'Only POST requests are allowed for the register resource\n'
        return http_bad_response

    prof_id = package['professor_id']
    module_id = package['module_code']
    try:
        prof = Professor.objects.get(professor_id = prof_id)
    except Professor.DoesNotExist:
        http_bad_response.content = 'Unknown professor id'
        return http_bad_response

    modules = Module.objects.filter(module_code = module_id)
    if len(modules) == 0:
        http_bad_response.content = 'Unknown module code'
        return http_bad_response

    json_package = {}
    for module in modules:
            json_package['module_name'] = module.module_name
            json_package['module_code'] = module.module_code
            
    rating = calc_average(prof_id, module_id)    
    json_package['professor_name'] = prof.name
    json_package['rating'] = rating

    json_package = json.dumps(json_package)

    return HttpResponse(json_package, content_type="application/json")

# POST
# rate prof in specific module instance (module code, year, semester)
@csrf_exempt
@login_required
def rate(request):
    http_bad_response = HttpResponseBadRequest()
    http_bad_response['Content-Type'] = 'text/plain'

    if request.method == 'POST':
        package = json.loads(request.body.decode('utf-8'))
    else:
        http_bad_response.content = 'Only POST requests are allowed for the register resource\n'
        return http_bad_response

    # Check rating within bounds, professor exists and module code exists
    if int(package['rating']) > 5 or int(package['rating']) < 1:
        http_bad_response.content = 'Only POST requests are allowed for the register resource\n'
        return http_bad_response

    try:
        prof = Professor.objects.get(professor_id = package['professor_id'])
    except Professor.DoesNotExist:
        http_bad_response.content = 'Unknown professor id'
        return http_bad_response

    try:
        module = Module.objects.get(module_code = package['module_code'], academic_year=package['year'], semester=package['semester'])
    except Module.MultipleObjectsReturned:
        http_bad_response.content = 'Multiple Modules found'
        return http_bad_response
    except Module.DoesNotExist:
        http_bad_response.content = 'Module Not Found'
        return http_bad_response

    rating = Rating(rating=package['rating'], professor_reference=prof, module_reference=module)
    rating.save()

    return HttpResponse('Rating received and added!')
    