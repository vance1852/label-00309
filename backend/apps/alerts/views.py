"""Alert views."""
import logging
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.core.response import success_response, error_response
from .models import AlertConfig, AlertRecipient
from .serializers import AlertConfigSerializer, AlertRecipientSerializer, TestEmailSerializer
from .services import AlertService

logger = logging.getLogger(__name__)


class AlertConfigView(APIView):
    """Alert configuration view."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get alert configuration."""
        config = AlertConfig.objects.first()
        if not config:
            return success_response(data=None)
        serializer = AlertConfigSerializer(config)
        return success_response(data=serializer.data)

    def put(self, request):
        """Update alert configuration."""
        config = AlertConfig.objects.first()
        if config:
            serializer = AlertConfigSerializer(config, data=request.data, partial=True)
        else:
            serializer = AlertConfigSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        
        serializer.save(updated_by=request.user)
        logger.info(f"User {request.user.username} updated alert configuration")
        return success_response(data=serializer.data, message='告警配置更新成功')


class AlertRecipientViewSet(viewsets.ModelViewSet):
    """Alert recipient viewset."""
    queryset = AlertRecipient.objects.all()
    serializer_class = AlertRecipientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        config = AlertConfig.objects.first()
        if config:
            return AlertRecipient.objects.filter(config=config)
        return AlertRecipient.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        config = AlertConfig.objects.first()
        if not config:
            return error_response(message='请先配置告警邮箱')
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        
        serializer.save(config=config)
        logger.info(f"User {request.user.username} added recipient: {serializer.data['email']}")
        return success_response(data=serializer.data, message='收件人添加成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        serializer.save()
        logger.info(f"User {request.user.username} updated recipient: {instance.email}")
        return success_response(data=serializer.data, message='收件人更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        email = instance.email
        instance.delete()
        logger.info(f"User {request.user.username} deleted recipient: {email}")
        return success_response(message='收件人删除成功')


class TestEmailView(APIView):
    """Test email view."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Send test email."""
        serializer = TestEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        
        try:
            service = AlertService()
            service.send_test_email(serializer.validated_data['recipient_email'])
            logger.info(f"User {request.user.username} sent test email")
            return success_response(message='测试邮件发送成功')
        except Exception as e:
            return error_response(message=str(e))
