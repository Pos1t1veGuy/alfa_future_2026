from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Profile, Product, LoanApplication, ApplicationHistory, Notification
User = get_user_model()

def user_payload(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return {'id': str(user.id), 'email': user.email, 'fullName': user.get_full_name() or user.username,
            'role': profile.role, 'company': profile.company_name or ('Альфа-Бизнес' if profile.role != 'client' else ''),
            'inn': profile.inn, 'phone': profile.phone}

class RegisterSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    company = serializers.CharField(max_length=255)
    inn = serializers.CharField(max_length=12, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    def validate_email(self, value):
        if User.objects.filter(username__iexact=value).exists() or User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Аккаунт с таким email уже существует.')
        return value.lower()
    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
    def create(self, validated):
        email = validated['email']
        name = validated['fullName']
        user = User.objects.create_user(username=email, email=email, password=validated['password'],
                                        first_name=name.split(' ')[0], last_name=' '.join(name.split(' ')[1:]))
        Profile.objects.create(user=user, role='client', company_name=validated['company'],
                               inn=validated.get('inn', ''), phone=validated.get('phone', ''))
        return user

class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        profile, _ = Profile.objects.get_or_create(user=user)
        token['role'] = profile.role
        token['name'] = user.get_full_name() or user.username
        return token
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = user_payload(self.user)
        data['accessToken'] = data.pop('access')
        data['refreshToken'] = data.pop('refresh')
        return data

class ProductSerializer(serializers.ModelSerializer):
    maxAmount = serializers.IntegerField(source='max_amount', read_only=True)
    minTermMonths = serializers.IntegerField(source='min_term_months', read_only=True)
    maxTermMonths = serializers.IntegerField(source='max_term_months', read_only=True)
    class Meta:
        model = Product
        fields = ['id','name','description','rate','maxAmount','term','icon','minTermMonths','maxTermMonths']

class ApplicationSerializer(serializers.ModelSerializer):
    productId = serializers.CharField(source='product_id', read_only=True)
    productName = serializers.CharField(source='product.name', read_only=True)
    termMonths = serializers.IntegerField(source='term_months')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    clientName = serializers.SerializerMethodField()
    historyItems = serializers.SerializerMethodField()
    managerName = serializers.SerializerMethodField()
    class Meta:
        model = LoanApplication
        fields = ['id','productId','productName','amount','termMonths','purpose','company','inn','contact_name','phone','status','createdAt','updatedAt','clientName','historyItems','managerName','decision_comment']
        read_only_fields = ['id','status','createdAt','updatedAt','clientName','historyItems','managerName','decision_comment']
    def get_clientName(self, obj): return obj.client.get_full_name() or obj.client.username
    def get_managerName(self, obj): return (obj.manager.get_full_name() or obj.manager.username) if obj.manager_id else ''
    def get_historyItems(self, obj):
        return [{'id': x.id, 'status': x.status, 'date': x.created_at, 'author': x.author, 'comment': x.comment} for x in obj.history.all()]

class NotificationSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    isRead = serializers.BooleanField(source='is_read', read_only=True)
    applicationId = serializers.CharField(source='application_id', read_only=True)
    class Meta:
        model = Notification
        fields = ['id','title','body','isRead','createdAt','applicationId']
