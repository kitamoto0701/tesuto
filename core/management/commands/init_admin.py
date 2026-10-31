from getpass import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from core.models import User, SeatLock
class Command(BaseCommand):
 help='初回管理者を対話式に作成（パスワードを引数・環境変数に残しません）'
 def handle(self,*args,**options):
  name=input('管理者ユーザー名: ').strip()
  password=getpass('パスワード（12文字以上）: ')
  if password!=getpass('確認: '):raise CommandError('パスワードが一致しません')
  u=User(username=name,role='admin')
  try:validate_password(password,u);u.full_clean(exclude=['password'])
  except ValidationError as e:raise CommandError(str(e))
  with transaction.atomic():
   SeatLock.objects.select_for_update().get(pk=1)
   if User.objects.exists():raise CommandError('初期管理者は作成済みです。画面からユーザー追加してください。')
   u.set_password(password);u.save()
  self.stdout.write(self.style.SUCCESS('管理者を作成しました'))
