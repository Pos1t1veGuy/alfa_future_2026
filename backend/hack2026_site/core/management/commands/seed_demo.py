from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Profile, Product
User = get_user_model()

class Command(BaseCommand):
    help = 'Create local demonstration data. Change demo credentials before any shared deployment.'
    def handle(self, *args, **options):
        manager, created = User.objects.get_or_create(username='manager@alfa.local', defaults={
            'email':'manager@alfa.local','first_name':'Алексей','last_name':'Смирнов','is_staff':True
        })
        if created: manager.set_password('DemoManager2026!'); manager.save()
        Profile.objects.update_or_create(user=manager, defaults={'role':'bank_manager','company_name':'Альфа-Бизнес'})
        products = [
            ('turnover','На пополнение оборотных средств','Закупайте товар, оплачивайте аренду и закрывайте кассовые разрывы.','от 18,5%',10000000,'до 36 месяцев','↻',3,36),
            ('equipment','На оборудование','Обновляйте технику и развивайте производство без изъятия всей суммы из оборота.','от 17,9%',15000000,'до 60 месяцев','⌘',6,60),
            ('universal','Универсальный кредит','Для задач бизнеса, когда нужна свободная цель финансирования.','от 19,5%',5000000,'до 24 месяцев','◈',3,24),
        ]
        for row in products:
            Product.objects.get_or_create(id=row[0], defaults={'name':row[1],'description':row[2],'rate':row[3],'max_amount':row[4],'term':row[5],'icon':row[6],'min_term_months':row[7],'max_term_months':row[8]})
        self.stdout.write(self.style.SUCCESS('Demo products are ready. Bank demo login: manager@alfa.local / DemoManager2026!'))
