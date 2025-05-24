import bcrypt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.mongo.user import User
from users.permissions import IsAuthenticated, IsAdminUser
from users.utils.jwt_utils import generate_token, invalidate_token
from users.utils.auth_utils import extract_user_from_request
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    data = request.data
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return Response({"error": "Missing required fields"}, status=400)

    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        user.save()
        return Response({"message": "User created successfully"}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login a user"""
    data = request.data
    username = data.get("username")
    password = data.get("password")

    if not all([username, password]):
        return Response({"error": "Missing username or password"}, status=400)

    user = User.objects(username=username).first()
    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return Response({"error": "Invalid credentials"}, status=401)

    token = generate_token(str(user.id))
    return Response({"token": token}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout a user"""
    try:
        token = request.META.get("HTTP_AUTHORIZATION").split(" ")[1]
        invalidate_token(token)
        return Response({"message": "Logged out successfully"}, status=200)
    except Exception:
        return Response({"error": "Invalid token"}, status=401)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_admin(request):
    """Create a new admin user"""
    try:
        # Check authentication first
        if not request.user or not getattr(request.user, 'is_authenticated', True):
            return Response({"error": "Authentication required"}, status=401)

        data = request.data
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return Response({"error": "Missing required fields"}, status=400)

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=True
        )
        user.save()
        return Response({"message": "Admin user created successfully"}, status=201)
    except AuthenticationFailed as e:
        return Response({"error": str(e)}, status=401)
    except Exception as e:
        print(f"Admin creation error: {e}")
        return Response({"error": str(e)}, status=400)

