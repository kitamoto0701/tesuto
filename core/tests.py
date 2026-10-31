from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Project, Schedule, Estimate, Invoice, Audit
from .forms import record_form
class ApplicationTests(TestCase):
 def setUp(self):
  self.admin=User.objects.create_user('admin',password='Test-Password-8492',role='admin')
  self.site=User.objects.create_user('site',password='Test-Password-8492',role='site')
  self.acc=User.objects.create_user('acc',password='Test-Password-8492',role='accounting')
  self.project=Project.objects.create(code='DEMO-1',name='架空工事',manager=self.site,start_date=date(2026,1,1),end_date=date(2026,12,31),contract=123456)
 def signin(self,user=None):self.client.force_login(user or self.admin)
 def schedule_data(self):return {'project':self.project.pk,'task':'基礎工事','owner':self.site.pk,'start_date':'2026-01-01','end_date':'2026-01-31','progress':0,'version':1}
 def test_auth_and_all_screens(self):
  self.assertEqual(self.client.get('/').status_code,302)
  self.signin()
  from .registry import MODULES
  for key in MODULES:
   self.assertEqual(self.client.get(f'/m/{key}/').status_code,200,key)
   self.assertEqual(self.client.get(f'/m/{key}/new/').status_code,200,key)
   self.assertEqual(self.client.get(f'/export/{key}/').status_code,200,key)
  for url in ['/','/users/','/audit/','/password/']:self.assertEqual(self.client.get(url).status_code,200)
 def test_role_boundaries(self):
  self.signin(self.site)
  for path in ['/users/','/audit/','/m/costs/','/export/costs/','/m/invoices/new/']:
   self.assertEqual(self.client.get(path).status_code,403,path)
  self.assertNotContains(self.client.get('/'),'123456')
  self.assertNotContains(self.client.get('/m/projects/'),'123456')
  self.assertNotContains(self.client.get('/export/projects/'),'123456')
  self.assertNotContains(self.client.get(f'/m/projects/{self.project.pk}/'),'name="contract"')
  self.signin(self.acc)
  self.assertEqual(self.client.get('/m/projects/new/').status_code,403)
  self.assertEqual(self.client.get('/m/costs/new/').status_code,200)
 def test_site_cannot_modify_contract(self):
  self.signin(self.site)
  self.client.post(f'/m/projects/{self.project.pk}/',{'code':'DEMO-1','name':'変更','manager':self.site.pk,'start_date':'2026-01-01','end_date':'2026-12-31','progress':0,'version':1,'contract':'999'})
  self.project.refresh_from_db();self.assertEqual(self.project.contract,123456);self.assertEqual(self.project.name,'変更')
 def test_dates_and_progress(self):
  cls=record_form(Schedule)
  data=self.schedule_data();data['end_date']='2025-01-01'
  self.assertFalse(cls(data).is_valid())
  data=self.schedule_data();data['progress']=101
  self.assertFalse(cls(data).is_valid())
 def test_estimate_decimal_calculation(self):
  self.signin()
  r=self.client.post('/m/estimates/new/',{'project':self.project.pk,'category':'基礎','description':'型枠','quantity':'3','unit':'m2','unit_price':'0.10','version':1})
  self.assertEqual(r.status_code,302);self.assertEqual(Estimate.objects.get().amount,Decimal('0.30'))
 def test_invalid_foreign_key_and_negative(self):
  data=self.schedule_data();data['project']=99999
  self.assertFalse(record_form(Schedule)(data).is_valid())
  form=record_form(Invoice)({'project':self.project.pk,'invoice_no':'I-1','invoice_date':'2026-01-01','due_date':'2026-01-31','amount':'-1','paid_amount':'0','version':1})
  self.assertFalse(form.is_valid())
 def test_overpayment(self):
  form=record_form(Invoice)({'project':self.project.pk,'invoice_no':'I-1','invoice_date':'2026-01-01','due_date':'2026-01-31','amount':'100','paid_amount':'101','version':1})
  self.assertFalse(form.is_valid())
 def test_conflicting_edit(self):
  self.signin();data=self.schedule_data();self.client.post('/m/schedules/new/',data)
  obj=Schedule.objects.get();url=f'/m/schedules/{obj.pk}/'
  data['progress']=25;self.assertEqual(self.client.post(url,data).status_code,302)
  data['progress']=50;self.assertEqual(self.client.post(url,data).status_code,409)
  obj.refresh_from_db();self.assertEqual(obj.progress,25)
 def test_ten_user_cap_and_reactivation(self):
  self.signin()
  for i in range(7):User.objects.create_user('u'+str(i))
  r=self.client.post('/users/',{'username':'eleven','role':'site','password1':'Long-Random-4321!','password2':'Long-Random-4321!'})
  self.assertContains(r,'最大10人');self.assertEqual(User.objects.filter(is_active=True).count(),10)
  extra=User.objects.create_user('disabled',is_active=False)
  self.assertEqual(self.client.post(f'/users/{extra.pk}/toggle/').status_code,400)
 def test_disabled_session(self):
  self.signin(self.site);self.site.is_active=False;self.site.save()
  self.assertEqual(self.client.get('/').status_code,302)
 def test_password_reset_revokes_session(self):
  other=Client();other.force_login(self.site);self.signin()
  self.client.post(f'/users/{self.site.pk}/password/',{'new_password1':'Changed-Secret-1892!','new_password2':'Changed-Secret-1892!'})
  self.assertEqual(other.get('/').status_code,302)
 def test_csrf_and_logout(self):
  c=Client(enforce_csrf_checks=True);c.force_login(self.admin)
  self.assertEqual(c.post('/m/schedules/new/',self.schedule_data()).status_code,403)
  self.assertEqual(c.post('/login/',{}).status_code,403)
  self.assertEqual(c.get('/logout/').status_code,405)
 def test_login_throttle(self):
  for i in range(5):self.client.post('/login/',{'username':'admin','password':'wrong'})
  self.assertEqual(self.client.post('/login/',{'username':'admin','password':'Test-Password-8492'}).status_code,429)
 def test_csv_formula_and_html_escape(self):
  self.project.name='=HYPERLINK("bad")';self.project.address='<script>alert(1)</script>';self.project.save()
  self.signin();self.assertContains(self.client.get('/export/projects/'),"'=HYPERLINK")
  self.assertNotContains(self.client.get('/m/projects/'),'<script>alert(1)</script>')
 def test_self_disable_and_audit(self):
  self.signin();self.assertEqual(self.client.post(f'/users/{self.admin.pk}/toggle/').status_code,400)
  self.client.post('/m/schedules/new/',self.schedule_data())
  self.assertTrue(Audit.objects.filter(action='create').exists())
 def test_health(self):self.assertEqual(self.client.get('/health/').json(),{'status':'ok'})

from concurrent.futures import ThreadPoolExecutor
from unittest import skipUnless
from django.db import connection, connections
from django.test import TransactionTestCase
from .models import SeatLock

@skipUnless(connection.vendor=='postgresql','PostgreSQL concurrency integration test')
class CapacityConcurrencyTests(TransactionTestCase):
 def test_two_admins_compete_for_last_seat(self):
  SeatLock.objects.get_or_create(pk=1)
  admin=User.objects.create_user('capacity_admin',password='Test-Password-8492',role='admin')
  for i in range(8):User.objects.create_user('capacity'+str(i))
  clients=[Client(),Client()]
  for c in clients:c.force_login(admin)
  from threading import Barrier
  barrier=Barrier(2)
  def add(index):
   try:
    barrier.wait(timeout=10)
    return clients[index].post('/users/',{'username':'new'+str(index),'role':'site','password1':'Unique-Password-1847!','password2':'Unique-Password-1847!'}).status_code
   finally:connections.close_all()
  with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(add,range(2)))
  self.assertEqual(sorted(statuses),[200,302])
  self.assertEqual(User.objects.filter(is_active=True).count(),10)
