from django.shortcuts import render
from rest_framework.views import APIView

from deliveries.mongo.delivery import Delivery
from users.mongo.user import User
from users.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from users.utils.auth_utils import extract_user_from_request

# Create your views here.

class DeliveryDetailView(APIView):
    """
    View to handle delivery details.
    This includes getting the details of a delivery and deleting a delivery.
    """

    def get_permissions(self):
        """
        Assign permissions based on the request method.
        - GET: No auth needed
        - POST, PUT, DELETE: IsAdminUser
        """
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsAuthenticated(), IsAdminUser()]
        return []

    def get(self, request, delivery_id):
        """
        Get the details of a delivery by its ID.
        Args:
            request: The HTTP request object.
            delivery_id: The ID of the delivery.
        Returns:
            Response: A response object with the delivery details or an error message.
        """
        delivery = Delivery.objects(delivery_id=delivery_id).first()
        if not delivery:
            return Response({"error": "Delivery not found"}, status=404)

        return Response(delivery.to_dict(), status=200)

    def delete(self, request, delivery_id):
        """
        Delete a delivery by its ID.
        Args:
            request: The HTTP request object.
            delivery_id: The ID of the delivery.
        Returns:
            Response: A response object with the status of the operation.
        """
        if not request.user.is_admin:
            return Response({"error": "Admin only"}, status=403)

        delivery = Delivery.objects(delivery_id=delivery_id).first()
        if not delivery:
            return Response({"error": "Delivery not found"}, status=404)

        delivery.delete()
        return Response({"message": "Delivery deleted"}, status=204)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_deliveries(request):
    """
    Get all deliveries for the authenticated user.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: A response object with the list of deliveries or an error message.
    """
    try:
        user = extract_user_from_request(request)
        deliveries = Delivery.objects(customer_id=user.username)
        return Response([delivery.to_dict() for delivery in deliveries], status=200)

    except Exception:
        return Response("User not found", status=404)

