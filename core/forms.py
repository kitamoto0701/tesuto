from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
class UserForm(UserCreationForm):
 class Meta(UserCreationForm.Meta):
  model=User
  fields=['username','first_name','last_name','role']
def record_form(model):
 class F(forms.ModelForm):
  version=forms.IntegerField(widget=forms.HiddenInput,initial=1)
  class Meta:
   fields='__all__'
   exclude=['updated_at']
  def __init__(self,*args,**kwargs):
   super().__init__(*args,**kwargs)
   for field in self.fields.values():
    if isinstance(field,forms.DateField):field.widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d')
  def clean(self):
   data=super().clean()
   if model.__name__=='Estimate' and data.get('quantity') is not None and data.get('unit_price') is not None:
    from decimal import Decimal, ROUND_HALF_UP
    amount=(data['quantity']*data['unit_price']).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    if amount>=Decimal('100000000000000'):raise forms.ValidationError('見積金額が上限を超えています。')
    self.instance.amount=amount
   return data
 F.Meta.model=model
 if model.__name__=='Estimate':F.Meta.exclude=['updated_at','amount']
 # ModelForm metaclass needs the model at class creation.
 return type(model.__name__+'Form',(F,),{'Meta':type('Meta',(F.Meta,),{'model':model})})
