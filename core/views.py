import csv, hashlib
from datetime import timedelta
from decimal import Decimal
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import login
from django.db import transaction
from django.db.models import Sum, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import User, SeatLock, Audit, LoginAttempt, Project, Schedule
from .registry import MODULES, FINANCIAL, allowed
from .forms import record_form, UserForm

def navigation(request):
 return {'nav':[(k,v[1]) for k,v in MODULES.items() if allowed(request.user,k)]}
def log(user,action,target):Audit.objects.create(actor=user,action=action,target=str(target))
def denied():return HttpResponse('この操作の権限がありません。',status=403)
def signin(request):
 form=AuthenticationForm(request,data=request.POST or None)
 if request.method=='POST':
  key=hashlib.sha256(request.POST.get('username','').strip().encode()).hexdigest()
  now=timezone.now()
  with transaction.atomic():
   row,_=LoginAttempt.objects.get_or_create(key=key,defaults={'until':now+timedelta(minutes=15)})
   row=LoginAttempt.objects.select_for_update().get(pk=key)
   if row.until<=now:row.count=0;row.until=now+timedelta(minutes=15)
   if row.count>=5:return HttpResponse('試行回数の上限です。15分後に再試行してください。',status=429)
   if form.is_valid():
    row.delete();login(request,form.get_user());log(request.user,'login','session')
    return redirect('/')
   row.count+=1;row.save()
 return render(request,'registration/login.html',{'form':form})

@login_required
def home(request):
 projects=Project.objects.select_related('manager').all()
 entries=[]
 for project in projects:
  item={'project':project}
  if request.user.role in ('admin','accounting'):
   for key,col in [('budgets','budget'),('orders','amount'),('costs','amount'),('invoices','amount')]:
    item[key]=MODULES[key][0].objects.filter(project=project).aggregate(x=Sum(col))['x'] or Decimal(0)
   item['paid']=MODULES['invoices'][0].objects.filter(project=project).aggregate(x=Sum('paid_amount'))['x'] or Decimal(0)
   item['profit']=project.contract-item['costs'];item['unpaid']=item['invoices']-item['paid']
  entries.append(item)
 return render(request,'home.html',{'entries':entries,'count':projects.count(),'late':Schedule.objects.filter(end_date__lt=timezone.localdate(),progress__lt=100).count(),'active':User.objects.filter(is_active=True).count(),'finance':request.user.role in ('admin','accounting')})

@login_required
def records(request,key):
 if key not in MODULES:return HttpResponse(status=404)
 if not allowed(request.user,key):return denied()
 model,title=MODULES[key]
 rows=model.objects.all()
 query=request.GET.get('q','').strip()
 if query:
  from django.db.models import Q, CharField
  search=Q()
  for field in model._meta.fields:
   if isinstance(field,CharField):search|=Q(**{field.name+'__icontains':query})
  rows=rows.filter(search)
 fields=[f for f in model._meta.fields if f.name not in ('version','updated_at') and not (request.user.role=='site' and f.name=='contract')]
 from django.core.paginator import Paginator
 page=Paginator(rows,50).get_page(request.GET.get('page'))
 data=[(r.pk,[getattr(r,f.name) for f in fields]) for r in page]
 return render(request,'records.html',{'key':key,'title':title,'headers':[f.verbose_name for f in fields],'rows':data,'page':page,'query':query,'write':allowed(request.user,key,True)})

@login_required
def edit(request,key,pk=None):
 if key not in MODULES:return HttpResponse(status=404)
 if not allowed(request.user,key,True):return denied()
 model,title=MODULES[key]
 obj=get_object_or_404(model,pk=pk) if pk else None
 cls=record_form(model)
 # Contract amounts are maintained by admin; site users cannot see or overwrite them.
 if key=='projects' and request.user.role=='site':cls.base_fields.pop('contract',None)
 form=cls(request.POST or None,instance=obj)
 status=200
 if request.method=='POST' and form.is_valid():
  with transaction.atomic():
   if pk:
    current=model.objects.select_for_update().get(pk=pk)
    if current.version!=form.cleaned_data['version']:
     form.add_error(None,'他の利用者が更新しました。一覧から開き直して再入力してください。');status=409
    else:
     # Conditional UPDATE protects against stale writes also on SQLite.
     changed=form.save(commit=False)
     values={f.attname:getattr(changed,f.attname) for f in model._meta.fields if f.name not in ('id','version','updated_at') and f.name in form.fields}
     if key=='estimates':values['amount']=changed.amount
     count=model.objects.filter(pk=pk,version=current.version).update(**values,version=F('version')+1,updated_at=timezone.now())
     if count!=1:return HttpResponse('更新が競合しました。再読込してください。',status=409)
     log(request.user,'update',f'{key}:{pk}');messages.success(request,'更新しました。');return redirect('records',key=key)
   else:
    record=form.save(commit=False);record.version=1;record.save();log(request.user,'create',f'{key}:{record.pk}')
    messages.success(request,'登録しました。');return redirect('records',key=key)
 return render(request,'form.html',{'form':form,'title':title+('を編集' if pk else 'を登録')},status=status)

@login_required
def export(request,key):
 if key not in MODULES:return HttpResponse(status=404)
 if not allowed(request.user,key):return denied()
 model,_=MODULES[key]
 fields=[f for f in model._meta.fields if not (request.user.role=='site' and f.name=='contract')]
 response=HttpResponse(content_type='text/csv; charset=utf-8-sig');response['Content-Disposition']=f'attachment; filename="{key}.csv"'
 response.write('\ufeff');writer=csv.writer(response);writer.writerow([f.verbose_name for f in fields])
 for r in model.objects.all().iterator():
  values=[]
  for f in fields:
   s=str(getattr(r,f.name))
   if s.lstrip().startswith(('=','+','-','@')) or s.startswith(('\t','\r','\n')):s="'"+s
   values.append(s)
  writer.writerow(values)
 log(request.user,'export',key)
 return response

@login_required
def users(request):
 if request.user.role!='admin':return denied()
 form=UserForm(request.POST or None)
 if request.method=='POST' and form.is_valid():
  with transaction.atomic():
   SeatLock.objects.select_for_update().get(pk=1)
   if User.objects.filter(is_active=True).count()>=10:form.add_error(None,'有効ユーザーは管理者を含め最大10人です。')
   else:
    u=form.save();log(request.user,'user.create',u.pk);return redirect('users')
 return render(request,'users.html',{'form':form,'users':User.objects.all().order_by('id')})

@login_required
@require_POST
def toggle_user(request,pk):
 if request.user.role!='admin':return denied()
 with transaction.atomic():
  SeatLock.objects.select_for_update().get(pk=1)
  u=get_object_or_404(User,pk=pk)
  if u.pk==request.user.pk:return HttpResponse('自分自身は無効化できません。',status=400)
  if not u.is_active and User.objects.filter(is_active=True).count()>=10:return HttpResponse('利用上限は10人です。',status=400)
  u.is_active=not u.is_active;u.save(update_fields=['is_active']);log(request.user,'user.active='+str(u.is_active),u.pk)
 return redirect('users')

@login_required
def reset_password(request,pk):
 if request.user.role!='admin':return denied()
 u=get_object_or_404(User,pk=pk);form=SetPasswordForm(u,request.POST or None)
 if request.method=='POST' and form.is_valid():
  with transaction.atomic():form.save();log(request.user,'user.password',u.pk)
  messages.success(request,'パスワードを変更しました。既存ログインは無効になります。');return redirect('users')
 return render(request,'form.html',{'form':form,'title':str(u)+'：パスワード変更'})

@login_required
def audit(request):
 if request.user.role!='admin':return denied()
 return render(request,'audit.html',{'logs':Audit.objects.select_related('actor').order_by('-id')[:200]})

def health(request):
 from django.db import connection
 with connection.cursor() as cursor:cursor.execute('SELECT 1')
 return JsonResponse({'status':'ok'})
