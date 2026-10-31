from . import models
MODULES={
 'projects': (models.Project, '工事案件'),
 'vendors': (models.Vendor, '協力業者'),
 'estimates': (models.Estimate, '見積'),
 'budgets': (models.Budget, '実行予算'),
 'orders': (models.Order, '発注'),
 'costs': (models.Cost, '原価'),
 'invoices': (models.Invoice, '請求・入金'),
 'schedules': (models.Schedule, '工程'),
 'reports': (models.Report, '日報'),
 'safety': (models.Safety, '安全管理'),
 'files': (models.FileRecord, '図面・写真台帳'),
}
FINANCIAL={"estimates","budgets","orders","costs","invoices"}
def allowed(user,key,write=False):
 if not user.is_authenticated or not user.is_active:return False
 if user.role=="admin":return True
 if key in FINANCIAL:return user.role=="accounting"
 if write:return user.role=="site" or key=="vendors"
 return True
