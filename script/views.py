﻿import os,random
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.core import serializers
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from django.contrib.auth.decorators import login_required,user_passes_test,permission_required
from autotester.script.models import Project,Module,Report,Api,Case,DbConfigure
from django.core.paginator import Paginator
import resttest
from autotester.script.resttest import Test,TestConfig,Validator
from djcelery.models import CrontabSchedule,PeriodicTask
import json
import datetime
import job
import util
#Enter home page
def home(request):
    return render_to_response("home.html",RequestContext(request))

#Enter login page
def sign_in(request):
    return render_to_response("login.html",RequestContext(request))

#Enter project list page
def projects_view(request):
    list = []
    data=Project.objects.all()
    for item in data:
        modules = Module.objects.filter(project=item)
        apitotal = 0
        success = 0
        failure = 0
        for module in modules:
            apis = Api.objects.filter(module=module)
            apitotal += len(apis)
            for api in apis:
                cases = Case.objects.filter(api=api)
                for case in cases:
                    success += Report.objects.filter(case=case,status=True).count()
                    failure += Report.objects.filter(case=case,status=False).count()
        dict={"item":item,"module_total":len(modules),"api_total":apitotal,"success":success,"failure":failure}
        list.append(dict)
    return render_to_response("projects.html",{"data":list},RequestContext(request))

#make projects statistic
def projects_statistic(request):
    list = []
    data=Project.objects.all()
    for item in data:
        modules = Module.objects.filter(project=item)
        apitotal = 0
        success = 0
        failure = 0
        casetotal = 0
        for module in modules:
            apis = Api.objects.filter(module=module)
            apitotal += len(apis)
            for api in apis:
                cases = Case.objects.filter(api=api)
                casetotal += len(cases)
                for case in cases:
                    success += Report.objects.filter(case=case,status=True).count()
                    failure += Report.objects.filter(case=case,status=False).count()
        itemlist = []
        itemlist.append(item)
        dict={"item":serializers.serialize('json', itemlist),"module_total":len(modules),"api_total":apitotal,"case_total":casetotal,"success":success,"failure":failure}
        list.append(dict)
    return HttpResponse(simplejson.dumps(list), mimetype="application/json")

#Enter one project detailed page
def project_view(request):
    project=Project.objects.get(id=request.REQUEST.get('id'))
    suites=Module.objects.filter(project=project)
    success = 0
    failure = 0
    casetotal = 0
    modules = list()
    for module in suites:
        module_success=0
        module_failure=0
        module_casetotal=0
        apis = Api.objects.filter(module=module)
        for api in apis:
            cases = Case.objects.filter(api=api)
            casetotal += len(cases)
            module_casetotal += len(cases)
            for case in cases:
                success += Report.objects.filter(case=case,status=True).count()
                module_success += Report.objects.filter(case=case,status=True).count()
                failure += Report.objects.filter(case=case,status=False).count()
                module_failure += Report.objects.filter(case=case,status=False).count()
        dict={"item":module,"success":module_success,"failure":module_failure,"total":module_casetotal}
        modules.append(dict)
        
    return render_to_response("project.html",{"project":project,"modules":modules,"success":success,"failure":failure,"case_total":casetotal},RequestContext(request))

def project_setting_view(request):
    project=Project.objects.get(id=request.REQUEST.get('id'))
    tname = project.name+"_task"
    try:
        ptask = PeriodicTask.objects.get(name=tname)
    except:
        print ("ptask is null")
        ptask = None
    try:
        dbconfigure = DbConfigure.objects.get(project=project)
    except:
        dbconfigure = None
    setting = dict()
    setting['task']=ptask
    setting['db']=dbconfigure
    return render_to_response("setting.html",{"project":project,"setting":setting},RequestContext(request))

@login_required
@permission_required('script.change_project')
def project_set(request):
    project = Project.objects.get(id=request.REQUEST.get('id'))
    crontab = CrontabSchedule(minute = request.REQUEST.get('minute'),hour = request.REQUEST.get('hour'))
    crontab.save()
    
    tname = project.name+"_task"
    try:
        ptask = PeriodicTask.objects.get(name=tname)
    except:
        print ("ptask is null")
        ptask = None
    if ptask is not None:
        ptask.crontab = crontab
        ptask.enabled = request.REQUEST.get('enable')
    else:
        ptask = PeriodicTask(name=project.name+"_task",task='autotester.script.task.executetest',crontab=crontab,args="["+request.REQUEST.get('id')+"]",enabled=request.REQUEST.get('enable'))
    ptask.save()

    address = request.REQUEST.get("address")
    username = request.REQUEST.get("username")
    password = request.REQUEST.get("password")
    dbname = request.REQUEST.get("dbname")
    port = request.REQUEST.get("port")
    file = request.FILES.get('sql', None)
    sql = None
    if file is not None:
        sql = file
    else:
        sql = request.REQUEST.get("sql")
        print (sql)
    try:
        dbconfigure = DbConfigure.objects.get(project=project)
    except:
        dbconfigure = None
 
    if dbconfigure is None:
        dbconfigure = DbConfigure(project=project,address=address,username=username,password=password,sql=sql,dbname=dbname,port=port)
    else:
        dbconfigure.address=address
        dbconfigure.username=username
        dbconfigure.password=password
        dbconfigure.sql=sql
        dbconfigure.dbname=dbname
        dbconfigure.port=port
    dbconfigure.save()
    return HttpResponseRedirect("/autotester/project?id="+request.REQUEST.get('id'))

#Enter api list page
def apis_view(request):
    module=Module.objects.get(id=request.REQUEST.get('mid'))
    apis=Api.objects.filter(module=module)
    return render_to_response("apis.html",{"module":module,"apis":apis},RequestContext(request))

#Enter case list view page with api id
def cases_view(request):
    api = Api.objects.get(id=request.REQUEST.get('aid'))
    cases = Case.objects.filter(api=api)
    return render_to_response('cases.html',{"api":api,"cases":cases},RequestContext(request))

#Enter reports view page
def reports_view(request):
    data=Project.objects.all()
    return render_to_response("reports.html",{"data":data},RequestContext(request))

#Open one page containing our information
def about_view(request):
    return render_to_response("about.html",RequestContext(request))

#Open one page for creating project
def project_create_view(request):
    return render_to_response("project_create.html",RequestContext(request))

def project_edit_view(request):
    project = Project.objects.get(id=request.REQUEST.get('id'))
    return render_to_response("project_edit.html",{"project":project},RequestContext(request))

@login_required
@permission_required('script.change_project')
def project_update(request):
    name = request.REQUEST.get("name")
    description = request.REQUEST.get("description")
    domain = request.REQUEST.get("domain")
    project = Project.objects.get(id=request.REQUEST.get('id'))
    project.name = name
    project.domain = domain
    project.description = description
    project.save()
    return HttpResponseRedirect("/autotester/projects")

#Enter one page for creating module with project id
def module_create_view(request):
    pid = request.REQUEST.get('pid')
    project = Project.objects.get(id=pid)
    return render_to_response("module_create.html",{"project":project},RequestContext(request))

#Enter one page for creating api
def api_create_view(request):
    mid = request.REQUEST.get('mid')
    module = Module.objects.get(id=mid)
    return render_to_response("api_create.html",{"module":module},RequestContext(request))

#Enter one page for creating case
def case_create_view(request):
    api = Api.objects.get(id=request.REQUEST.get('aid'))
    print (api.method)
    return render_to_response("case_create.html",{"api":api},RequestContext(request))

#Execute operation for insert one project into table
@login_required
@permission_required('script.add_project')
def project_save(request):
    user = request.user;
    name = request.REQUEST.get("name")
    description = request.REQUEST.get("description")
    domain = request.REQUEST.get("domain")
    project = Project(created_user=user,name=name,description=description,domain=domain)
    project.save()
    return HttpResponseRedirect('/autotester/projects')

#Execute operation for insert one module into table
@login_required
@permission_required('script.add_module')
def module_save(request):
    project = Project.objects.get(id=request.REQUEST.get('pid'))
    user = request.user;
    name = request.REQUEST.get('name')
    module = Module(project=project,created_user=user,name=name)
    module.save()
    return HttpResponseRedirect('/autotester/project?id='+str(project.id))

#Execute operation for insert one API into table
@login_required
@permission_required('script.add_api')
def api_save(request):
    module = Module.objects.get(id=request.REQUEST.get('mid'))
    user = request.user
    url = request.REQUEST.get('url')
    name = request.REQUEST.get('name')
    method = request.REQUEST.get('method')
    headers = request.REQUEST.get('headers')
    api = Api(module=module,created_user=user,url=url,method=method,name=name,headers=headers)
    api.save()
    return HttpResponseRedirect('/autotester/apis?mid='+str(module.id))

#Enter one page for editing api information
def api_edit_view(request):
    api = Api.objects.get(id=request.REQUEST.get('id'))
    return render_to_response('api_edit.html',{'api':api},RequestContext(request))

#Execute operation for updating api information
@login_required
@permission_required('script.change_api')
def api_update(request):
    api = Api.objects.get(id=request.REQUEST.get('id'))
    api.name = request.REQUEST.get('name')
    api.url = request.REQUEST.get('url')
    api.method = request.REQUEST.get('method')
    api.headers = request.REQUEST.get('headers')
    api.save()
    return HttpResponseRedirect('/autotester/apis?mid='+str(api.module.id))

#Open page for editing case with api id
def case_edit_view(request):
    case = Case.objects.get(id=request.REQUEST.get('id'))
    return render_to_response('case_edit.html',{'case':case},RequestContext(request))

#Execute update operation for the given case
@login_required
@permission_required('script.change_case')
def case_update(request):
    case = Case.objects.get(id=request.REQUEST.get('id'))
    case.body = request.REQUEST.get('body')
    case.expected_status = request.REQUEST.get('expected_status')
    case.expected = request.REQUEST.get('expected')
    case.check_sql = request.REQUEST.get('check_sql')
    case.save()
    return HttpResponseRedirect('/autotester/cases?aid='+str(case.api.id))

#Execute operation for insert one case into table
@login_required
@permission_required('script.add_case')
def case_save(request):
    api = Api.objects.get(id=request.REQUEST.get('aid'))
    body = request.REQUEST.get('body')
    expected_status = request.REQUEST.get('expected_status')
    expected = request.REQUEST.get('expected')
    user = request.user
    check_sql = request.REQUEST.get('check_sql')
    case = Case(api=api,body=body,expected_status=expected_status,expected=expected,created_user=user,check_sql=check_sql)
    case.save()
    return HttpResponseRedirect('/autotester/cases?aid='+str(api.id))
@login_required
@permission_required('script.change_project')
def project_inactive(request):
    project = Project.objects.get(id=request.REQUEST.get('id'))
    project.status = True
    project.save()
    return HttpResponseRedirect('/autotester/projects')
    
@login_required
@permission_required('script.change_project')
def project_active(request):
    project = Project.objects.get(id=request.REQUEST.get('id'))
    project.status = False
    project.save()
    return HttpResponseRedirect('/autotester/projects')

@login_required
@permission_required('script.change_module')
def module_inactive(request):
    module = Module.objects.get(id=request.REQUEST.get('id'))
    module.status = True
    module.save()
    return HttpResponseRedirect('/autotester/project?id='+str(module.project.id))

@login_required
@permission_required('script.change_module')
def module_active(request):
    module = Module.objects.get(id=request.REQUEST.get('id'))
    module.status = False
    module.save()
    return HttpResponseRedirect('/autotester/project?id='+str(module.project.id))

@login_required
@permission_required('script.change_api')
def api_inactive(request):
    api = Api.objects.get(id=request.REQUEST.get('id'))
    api.status = True
    api.save()
    return HttpResponseRedirect('/autotester/apis?mid='+str(api.module.id))

@login_required
@permission_required('script.change_api')
def api_active(request):
    api = Api.objects.get(id=request.REQUEST.get('id'))
    api.status = False
    api.save()
    return HttpResponseRedirect('/autotester/apis?mid='+str(api.module.id))

@login_required
@permission_required('script.change_case')
def case_inactive(request):
    case = Case.objects.get(id=request.REQUEST.get('id'))
    case.status = True
    case.save()
    return HttpResponseRedirect('/autotester/cases?aid='+str(case.api.id))

@login_required
@permission_required('script.change_case')
def case_active(request):
    case = Case.objects.get(id=request.REQUEST.get('id'))
    case.status = False
    case.save()
    return HttpResponseRedirect('/autotester/cases?aid='+str(case.api.id))

def case_report_view(request):
    case = Case.objects.get(id=request.REQUEST.get('id'))
    reports = Report.objects.filter(case=case)
    return render_to_response('case_report.html',{'case':case,'reports':reports},RequestContext(request))

def api_report_view(request):
    api = Api.objects.get(id=request.REQUEST.get('aid'))
    cases = Case.objects.filter(api=api)
    
    reports = list()
    for case in cases:
        reports.extend(Report.objects.filter(case=case))

    return render_to_response('api_report.html',{'api':api,'reports':reports},RequestContext(request))

def all_report_view(request):
    reports = list()
    cases = list()
    project = Project.objects.get(id=request.REQUEST.get('pid'))
    modules = Module.objects.filter(project=project)
    if request.REQUEST.get('filter')=='success':
        for module in modules:
            apis = Api.objects.filter(module=module)
            for api in apis:
                cases.extend(Case.objects.filter(api=api))
        for case in cases:
            reports.extend(Report.objects.filter(case=case,status=True))
    elif request.REQUEST.get('filter')=='failure':
        for module in modules:
            apis = Api.objects.filter(module=module)
            for api in apis:
                cases.extend(Case.objects.filter(api=api))
        for case in cases:
            reports.extend(Report.objects.filter(case=case,status=False))
    else:
        for module in modules:
            apis = Api.objects.filter(module=module)
            for api in apis:
                cases.extend(Case.objects.filter(api=api))
        for case in cases:
            reports.extend(Report.objects.filter(case=case))

    return render_to_response('all_report.html',{'project':project,'reports':reports},RequestContext(request))

#Test one case and generate report
@login_required
@permission_required('script.add_report')
def case_test(request):
    
    #Query all required information for testing
    case = Case.objects.get(id=request.REQUEST.get('id'))
    job.test(case,request.user)
    return HttpResponseRedirect('/autotester/case/report?id='+str(case.id))

#Test multi cases and generate report
@permission_required('script.add_report')
@login_required
def multi_case_test(request):
    api = Api.objects.get(id=request.REQUEST.get('aid'))
    cases = Case.objects.filter(api=api)

    for case in cases:
        job.test(case,request.user)
    
    return HttpResponseRedirect('/autotester/api/report?aid='+str(api.id))

#Test multi cases and generate report
@permission_required('script.add_report')
@login_required
def all_test(request):
    project = Project.objects.get(id=request.REQUEST.get('pid'))

    #init database
    try:
        dbconfigure = DbConfigure.objects.get(project=project)
        job.run_sql_file(dbconfigure.sql,dbconfigure.address,dbconfigure.username,dbconfigure.password)
    except:
        print ("Has not configured sql script")
    modules = Module.objects.filter(project=project)
    for module in modules:
        apis = Api.objects.filter(module=module)
        for api in apis:
            cases = Case.objects.filter(api=api)

            for case in cases:
                job.test(case,request.user)
    return HttpResponseRedirect('/autotester/all/report?pid='+str(project.id))

def project_report(request):
    project = Project.objects.get(id=request.REQUEST.get('id'))
    modules = Module.objects.filter(project=project)
    
    apis = list()
    for module in modules:
        apis.extend(Api.objects.filter(module=module))
    
    cases = list()
    for api in apis:
        cases.extend(Case.objects.filter(api=api))
    
    reports = list()
    for case in cases:
        reports.extend(Report.objects.filter(case=case))
    
    p = Paginator(reports, 10)
    total = p.count
    num_pages =  p.num_pages 
    data = p.page(request.REQUEST.get('pn')).object_list     

    result = {"data":serializers.serialize('json', data),"total":total,"numpages":num_pages}
    return HttpResponse(simplejson.dumps(result), mimetype="application/json")