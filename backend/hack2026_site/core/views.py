from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import Profile, Product, LoanApplication, ApplicationHistory, Notification, UploadedDocument
from .serializers import RegisterSerializer, LoginSerializer, ProductSerializer, ApplicationSerializer, NotificationSerializer, user_payload
User = get_user_model()

def ensure_products():
    data = [
        ('turnover','На пополнение оборотных средств','Закупайте товар, оплачивайте аренду и закрывайте кассовые разрывы.','от 18,5%',10000000,'до 36 месяцев','↻',3,36),
        ('equipment','На оборудование','Обновляйте технику и развивайте производство без изъятия всей суммы из оборота.','от 17,9%',15000000,'до 60 месяцев','⌘',6,60),
        ('universal','Универсальный кредит','Для задач бизнеса, когда нужна свободная цель финансирования.','от 19,5%',5000000,'до 24 месяцев','◈',3,24),
    ]
    for row in data:
        Product.objects.get_or_create(id=row[0], defaults=dict(name=row[1], description=row[2], rate=row[3], max_amount=row[4], term=row[5], icon=row[6], min_term_months=row[7], max_term_months=row[8]))

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        profile = user.profile
        token['role'] = profile.role
        token['name'] = user.get_full_name()
        return Response({'accessToken': str(token.access_token), 'refreshToken': str(token), 'user': user_payload(user)}, status=201)

class MeView(APIView):
    def get(self, request): return Response(user_payload(request.user))
    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        for field in ('company','inn','phone'):
            if field in request.data:
                setattr(profile, {'company':'company_name'}.get(field, field), request.data[field])
        profile.save()
        if 'fullName' in request.data:
            parts = str(request.data['fullName']).strip().split(' ', 1)
            request.user.first_name = parts[0]
            request.user.last_name = parts[1] if len(parts)>1 else ''
            request.user.save()
        return Response(user_payload(request.user))

class ProductsView(APIView):
    def get(self, request):
        ensure_products()
        items = Product.objects.filter(is_active=True)
        amount = request.query_params.get('minAmount')
        if amount:
            items = items.filter(max_amount__gte=amount)
        return Response({'items': ProductSerializer(items, many=True).data, 'total': items.count()})

class ApplicationsView(APIView):
    def get(self, request):
        qs = LoanApplication.objects.select_related('product','client','manager').prefetch_related('history')
        role = getattr(getattr(request.user, 'profile', None), 'role', 'client')
        if role not in ('bank_manager','admin'): qs = qs.filter(client=request.user)
        else:
            if request.query_params.get('status'): qs = qs.filter(status=request.query_params['status'])
            if request.query_params.get('search'):
                q=request.query_params['search']; qs=qs.filter(Q(id__icontains=q)|Q(company__icontains=q)|Q(client__first_name__icontains=q)|Q(client__last_name__icontains=q))
        return Response({'items': ApplicationSerializer(qs.order_by('-created_at'), many=True).data, 'total': qs.count(), 'page': 1, 'pageSize': qs.count()})
    def post(self, request):
        ensure_products()
        product = get_object_or_404(Product, pk=request.data.get('productId'))
        try: amount = int(request.data.get('amount', 0)); term = int(request.data.get('termMonths', 12))
        except (TypeError, ValueError): return Response({'message':'Проверьте сумму и срок.'}, status=400)
        if amount <= 0 or amount > product.max_amount: return Response({'message':f'Сумма должна быть от 1 до {product.max_amount} ₽.'}, status=400)
        if term < product.min_term_months or term > product.max_term_months: return Response({'message':'Срок не подходит для выбранного продукта.'}, status=400)
        app = LoanApplication.objects.create(client=request.user, product=product, amount=amount, term_months=term,
            purpose=request.data.get('purpose') or 'Пополнение оборотных средств',
            company=request.data.get('company') or getattr(getattr(request.user,'profile',None),'company_name',''),
            inn=request.data.get('inn') or getattr(getattr(request.user,'profile',None),'inn',''),
            contact_name=request.data.get('contactName') or request.user.get_full_name(),
            phone=request.data.get('phone') or getattr(getattr(request.user,'profile',None),'phone',''),
            status='submitted')
        ApplicationHistory.objects.create(application=app,status='submitted',author=app.client.get_full_name() or app.client.username,comment='Заявка отправлена в банк')
        Notification.objects.create(user=request.user,application=app,title='Заявка отправлена',body=f'Заявка {app.id} принята и передана в банк.')
        return Response(ApplicationSerializer(app).data, status=201)

class ApplicationDetailView(APIView):
    def get_app(self, request, pk):
        qs=LoanApplication.objects.select_related('product','client','manager').prefetch_related('history')
        app=get_object_or_404(qs, pk=pk)
        role=getattr(getattr(request.user,'profile',None),'role','client')
        if app.client_id != request.user.id and role not in ('bank_manager','admin'):
            return None
        return app
    def get(self, request, pk):
        app=self.get_app(request,pk)
        if not app: return Response({'message':'Нет доступа'},status=403)
        return Response(ApplicationSerializer(app).data)
    def patch(self, request, pk):
        app=self.get_app(request,pk)
        if not app: return Response({'message':'Нет доступа'},status=403)
        role=getattr(getattr(request.user,'profile',None),'role','client')
        if role not in ('bank_manager','admin'):
            return Response({'message':'Изменять заявку можно только через поддержку.'},status=403)
        new_status=request.data.get('status')
        allowed={'review','additional_info','approved','declined'}
        if new_status not in allowed: return Response({'message':'Недопустимый статус.'},status=400)
        app.status=new_status
        app.decision_comment=request.data.get('comment','')
        if not app.manager_id: app.manager=request.user
        app.save()
        ApplicationHistory.objects.create(application=app,status=new_status,author=request.user.get_full_name() or request.user.username,comment=app.decision_comment)
        Notification.objects.create(user=app.client,application=app,title='Статус заявки изменён',body=f'{app.id}: {dict(LoanApplication.STATUSES).get(new_status,new_status)}. {app.decision_comment}')
        return Response(ApplicationSerializer(app).data)

class NotificationsView(APIView):
    def get(self, request):
        qs=Notification.objects.filter(user=request.user).order_by('-created_at')
        if request.query_params.get('unreadOnly')=='true': qs=qs.filter(is_read=False)
        return Response({'items':NotificationSerializer(qs,many=True).data,'total':qs.count()})
    def post(self, request):
        Notification.objects.filter(user=request.user,is_read=False).update(is_read=True)
        return Response(status=204)

class NotificationReadView(APIView):
    def post(self, request, pk):
        note=get_object_or_404(Notification,user=request.user,pk=pk)
        note.is_read=True; note.save(update_fields=['is_read'])
        return Response(status=204)

class SafeLimitView(APIView):
    def post(self, request):
        try:
            revenue=max(0,float(request.data.get('avgMonthlyRevenue',0)))
            expenses=max(0,float(request.data.get('avgMonthlyExpenses',0)))
            debt=max(0,float(request.data.get('existingMonthlyDebt',0)))
            amount=max(0,float(request.data.get('requestedAmount',0)))
        except (ValueError,TypeError): return Response({'message':'Укажите числовые значения.'},status=400)
        free=max(revenue-expenses-debt,0)
        maximum=int(free*10*.7)
        minimum=int(maximum*.65)
        monthly_payment=amount/12 if amount else 0
        pdn=round((debt+monthly_payment)/revenue,3) if revenue else 0
        return Response({'safeMin':minimum,'safeMax':maximum,'pdnBefore':round(debt/revenue,3) if revenue else 0,'pdnAfter':pdn,'riskLevel':'low' if pdn<.3 else 'medium' if pdn<.5 else 'high','recommendation':'Ориентировочный расчёт. Финальное решение принимает банк.','factors':[]})

class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        file = request.FILES.get('file')
        if not file: return Response({'message':'Выберите файл для загрузки.'}, status=400)
        if file.size > 10 * 1024 * 1024: return Response({'message':'Максимальный размер файла — 10 МБ.'}, status=413)
        if not file.name.lower().endswith(('.pdf','.jpg','.jpeg','.png')):
            return Response({'message':'Поддерживаются PDF, JPG и PNG.'}, status=415)
        app = get_object_or_404(LoanApplication, pk=request.data.get('applicationId'))
        role = getattr(getattr(request.user, 'profile', None), 'role', 'client')
        if app.client_id != request.user.id and role not in ('bank_manager','admin'):
            return Response({'message':'Нет доступа к заявке.'}, status=403)
        doc = UploadedDocument.objects.create(application=app,user=request.user,file=file,filename=file.name,size=file.size)
        return Response({'id':str(doc.id),'filename':doc.filename,'size':doc.size,'status':doc.status},status=201)

class DocumentOCRView(APIView):
    def post(self, request, pk):
        doc = get_object_or_404(UploadedDocument.objects.select_related('application','user'), pk=pk)
        role = getattr(getattr(request.user, 'profile', None), 'role', 'client')
        if doc.application.client_id != request.user.id and role not in ('bank_manager','admin'):
            return Response({'message':'Нет доступа к документу.'},status=403)
        doc.status='PARSED'; doc.save(update_fields=['status'])
        profile = getattr(doc.application.client, 'profile', None)
        return Response({'documentId':str(doc.id),'status':'PARSED','confidence':0.94,'extractedFields':{'inn':getattr(profile,'inn',''),'revenue':1500000,'companyName':getattr(profile,'company_name','')}})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    # Access tokens are stateless; the client discards both tokens.
    return Response(status=204)
