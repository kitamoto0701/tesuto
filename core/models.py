from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class User(AbstractUser):
 role=models.CharField('権限',max_length=20,choices=[('admin','管理者'),('site','工事担当'),('accounting','経理担当')],default='site')
 def __str__(self): return self.get_full_name() or self.username
class SeatLock(models.Model):
 pass
class LoginAttempt(models.Model):
 key=models.CharField(max_length=64,primary_key=True)
 count=models.PositiveIntegerField(default=0)
 until=models.DateTimeField()
class Audit(models.Model):
 actor=models.ForeignKey(User,null=True,on_delete=models.SET_NULL)
 action=models.CharField(max_length=100)
 target=models.CharField(max_length=100)
 created_at=models.DateTimeField(auto_now_add=True)
class Record(models.Model):
 version=models.PositiveIntegerField(default=1)
 updated_at=models.DateTimeField(auto_now=True)
 class Meta: abstract=True
 def clean(self):
  super().clean()
  if hasattr(self,'start_date') and self.start_date and self.end_date and self.start_date>self.end_date:
   raise ValidationError('終了日は開始日以降にしてください。')
 def __str__(self): return str(getattr(self,'name',None) or getattr(self,'task',None) or getattr(self,'description',None) or f'#{self.pk}')

class Project(Record):
 code=models.CharField('工事番号',max_length=200,blank=False,unique=True)
 name=models.CharField('工事名称',max_length=200,blank=False,unique=False)
 address=models.CharField('所在地',max_length=200,blank=True,unique=False)
 client=models.CharField('発注者',max_length=200,blank=True,unique=False)
 manager=models.ForeignKey(User,verbose_name='担当者',on_delete=models.PROTECT,limit_choices_to={'is_active':True})
 start_date=models.DateField('着工日')
 end_date=models.DateField('竣工日')
 contract=models.DecimalField('契約額',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 status=models.CharField('状況',max_length=200,blank=True,unique=False)
 progress=models.PositiveIntegerField('進捗％',default=0,validators=[MaxValueValidator(100)])
 class Meta:
  verbose_name='工事案件'
  ordering=['-id']
class Vendor(Record):
 name=models.CharField('会社名',max_length=200,blank=False,unique=False)
 contact=models.CharField('担当者',max_length=200,blank=True,unique=False)
 phone=models.CharField('電話番号',max_length=200,blank=True,unique=False)
 email=models.EmailField('メール',blank=True)
 trade=models.CharField('業種',max_length=200,blank=True,unique=False)
 class Meta:
  verbose_name='協力業者'
  ordering=['-id']
class Estimate(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 category=models.CharField('工種',max_length=200,blank=True,unique=False)
 description=models.CharField('品目',max_length=200,blank=False,unique=False)
 quantity=models.DecimalField('数量',max_digits=16,decimal_places=3,default=0,validators=[MinValueValidator(0)])
 unit=models.CharField('単位',max_length=200,blank=True,unique=False)
 unit_price=models.DecimalField('単価',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 amount=models.DecimalField('金額',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 class Meta:
  verbose_name='見積'
  ordering=['-id']
class Budget(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 category=models.CharField('工種',max_length=200,blank=True,unique=False)
 budget=models.DecimalField('予算額',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 class Meta:
  verbose_name='実行予算'
  ordering=['-id']
class Order(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 vendor=models.ForeignKey(Vendor,verbose_name='協力会社',on_delete=models.PROTECT)
 order_date=models.DateField('発注日')
 description=models.CharField('発注内容',max_length=200,blank=False,unique=False)
 amount=models.DecimalField('発注額',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 status=models.CharField('状況',max_length=200,blank=True,unique=False)
 class Meta:
  verbose_name='発注'
  ordering=['-id']
class Cost(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 cost_date=models.DateField('計上日')
 category=models.CharField('工種',max_length=200,blank=True,unique=False)
 description=models.CharField('内容',max_length=200,blank=False,unique=False)
 cost_type=models.CharField('費目',max_length=200,blank=True,unique=False)
 amount=models.DecimalField('金額',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 class Meta:
  verbose_name='原価'
  ordering=['-id']
class Invoice(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 invoice_no=models.CharField('請求番号',max_length=200,blank=False,unique=False)
 invoice_date=models.DateField('請求日')
 amount=models.DecimalField('請求額',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 paid_amount=models.DecimalField('入金額',max_digits=16,decimal_places=2,default=0,validators=[MinValueValidator(0)])
 due_date=models.DateField('入金予定日')
 def clean(self):
  super().clean()
  if self.paid_amount is not None and self.amount is not None and self.paid_amount>self.amount: raise ValidationError('入金額は請求額以下にしてください。')
 class Meta:
  verbose_name='請求・入金'
  ordering=['-id']
class Schedule(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 task=models.CharField('作業項目',max_length=200,blank=False,unique=False)
 owner=models.ForeignKey(User,verbose_name='担当',on_delete=models.PROTECT,limit_choices_to={'is_active':True})
 start_date=models.DateField('開始日')
 end_date=models.DateField('終了日')
 progress=models.PositiveIntegerField('進捗％',default=0,validators=[MaxValueValidator(100)])
 class Meta:
  verbose_name='工程'
  ordering=['-id']
class Report(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 work_date=models.DateField('作業日')
 weather=models.CharField('天候',max_length=200,blank=True,unique=False)
 workers=models.PositiveIntegerField('人数',default=0,validators=[MaxValueValidator(10000)])
 work=models.CharField('作業内容',max_length=2000,blank=True,unique=False)
 safety=models.CharField('安全・KY',max_length=2000,blank=True,unique=False)
 class Meta:
  verbose_name='日報'
  ordering=['-id']
class Safety(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 record_date=models.DateField('記録日')
 item=models.CharField('確認事項',max_length=200,blank=True,unique=False)
 responsible=models.ForeignKey(User,verbose_name='担当者',on_delete=models.PROTECT,limit_choices_to={'is_active':True})
 status=models.CharField('状況',max_length=200,blank=True,unique=False)
 class Meta:
  verbose_name='安全管理'
  ordering=['-id']
class FileRecord(Record):
 project=models.ForeignKey(Project,verbose_name='工事案件',on_delete=models.PROTECT)
 record_date=models.DateField('登録日')
 category=models.CharField('区分',max_length=200,blank=True,unique=False)
 title=models.CharField('名称',max_length=200,blank=False,unique=False)
 file_path=models.CharField('保存先参照',max_length=2000,blank=True,unique=False)
 class Meta:
  verbose_name='図面・写真台帳'
  ordering=['-id']
