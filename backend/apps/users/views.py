"""User views."""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.response import success_response, error_response
from .serializers import LoginSerializer, UserSerializer, PasswordChangeSerializer

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """User login view."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"User {user.username} logged in successfully")
        
        return success_response(data={
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }, message='登录成功')


class LogoutView(APIView):
    """User logout view."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        
        logger.info(f"User {request.user.username} logged out")
        return success_response(message='登出成功')


class ProfileView(APIView):
    """User profile view."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(data=serializer.data)


class PasswordChangeView(APIView):
    """Password change view."""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=list(serializer.errors.values())[0][0])
        
        if not request.user.check_password(serializer.validated_data['old_password']):
            return error_response(message='原密码错误')
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        logger.info(f"User {request.user.username} changed password")
        return success_response(message='密码修改成功')
