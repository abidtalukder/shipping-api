import bcrypt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.mongo.user import User
from users.permissions import IsAuthenticated, IsAdminUser
from users.utils.jwt_utils import generate_token
from users.utils.auth_utils import extract_user_from_request

class RegisterView(APIView):
    def post(self, request):
        data = request.data
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return Response({"error": "Missing fields"}, status=400)

        if User.objects(username=username).first():
            return Response({"error": "Username already exists"}, status=400)

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(username=username, email=email, password_hash=hashed_pw)
        user.save()

        return Response({"message": "User registered"}, status=201)

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_admin_user(request):
    """
    Create an admin user if it doesn't exist.

    Args:
        request: The HTTP request object.
    Returns:
        Response: A response object with the status of the operation.
    """
    creator = extract_user_from_request(request)
    data = request.data
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return Response({"error": "Missing fields"}, status=400)

    if User.objects(username=username).first():
        user = User.objects(username=username).first()
        user.is_admin = True
        user.save()

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username=username, email=email, password_hash=hashed_pw, is_admin=True)
    user.save()
    return Response({"message": "Admin user created"}, status=201)



class LoginView(APIView):
    def post(self, request):
        data = request.data
        username = data.get("username")
        password = data.get("password")

        user = User.objects(username=username).first()
        if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return Response({"error": "Invalid credentials"}, status=401)

        token = generate_token(user.id)
        return Response({"token": token})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # placeholder for logout logic
    return Response({"message": "Logged out successfully"})

