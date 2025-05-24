from django.shortcuts import render
from rest_framework.views import APIView
from deliveries.mongo.delivery import Delivery, StatusHistory, VALID_STATUSES
from users.mongo.user import User
from users.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from users.utils.auth_utils import extract_user_from_request
from deliveries.utils.validators import validate_lat_lon_input
from datetime import datetime, timezone
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed

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
        if self.request.method in ['PUT', 'DELETE', 'POST']:
            return [IsAuthenticated(), IsAdminUser()]
        return [AllowAny()]

    def handle_exception(self, exc):
        if isinstance(exc, AuthenticationFailed):
            return Response({"error": str(exc)}, status=401)
        return super().handle_exception(exc)

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
        try:
            delivery = Delivery.objects(delivery_id=delivery_id).first()
            if not delivery:
                return Response({"error": "Delivery not found"}, status=404)

            delivery.delete()
            return Response({"message": "Delivery deleted"}, status=204)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=401)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def put(self, request, delivery_id):
        try:
            data = request.data
            location = data.get("location")

            # Validate format
            if not isinstance(location, dict):
                return Response({"error": "Location must be a dict"}, status=400)

            if location.get("type") != "Point":
                return Response({"error": "Location 'type' must be 'Point'"}, status=400)

            coords = location.get("coordinates")
            if not isinstance(coords, list) or len(coords) != 2:
                return Response({"error": "'coordinates' must be a [longitude, latitude] list"}, status=400)

            try:
                lon, lat = float(coords[0]), float(coords[1])
            except (ValueError, TypeError):
                return Response({"error": "Coordinates must be numeric"}, status=400)

            delivery = Delivery.objects(delivery_id=delivery_id).first()
            if not delivery:
                return Response({"error": "Delivery not found"}, status=404)

            delivery.current_location = {
                "type": "Point",
                "coordinates": [lon, lat]
            }
            delivery.last_updated = datetime.now(timezone.utc)
            delivery.save()

            return Response({"message": "Location updated"}, status=200)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=401)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class MyDeliveriesView(APIView):
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        if isinstance(exc, AuthenticationFailed):
            return Response({"error": str(exc)}, status=401)
        return super().handle_exception(exc)

    def get(self, request):
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
            return Response({"error": "User not found"}, status=404)


# ADMIN ROUTES
class DeliveryListCreate(APIView):
    """
    View to handle listing and creating deliveries.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def handle_exception(self, exc):
        if isinstance(exc, AuthenticationFailed):
            return Response({"error": str(exc)}, status=401)
        return super().handle_exception(exc)

    def get(self, request):
        """
        Get a list of all deliveries.
        Args:
            request: The HTTP request object.
        Returns:
            Response: A response object with the list of deliveries.
        """
        deliveries = Delivery.objects()
        return Response([delivery.to_dict() for delivery in deliveries], status=200)

    def post(self, request):
        try:
            data = request.data
            title = data.get("title")
            status = data.get("status")
            customer_id = data.get("customer_id")
            recipient_name = data.get("recipient_name")
            current_location = data.get("current_location")
            destination = data.get("destination")

            if not all([title, status, recipient_name, current_location]):
                return Response({"error": "Missing fields"}, status=400)

            id = f"DEL{random.randint(100000, 999999)}"
            while Delivery.objects(delivery_id=id).first():
                id = f"DEL{random.randint(100000, 999999)}"

            try:
                status_history = StatusHistory(
                    status=status,
                    location=current_location
                )
            except Exception:
                return Response({"error": "Invalid location format or status chosen"}, status=400)
            try:
                delivery = Delivery(
                    delivery_id=id,
                    title=title,
                    status=status,
                    customer_id=customer_id,
                    recipient_name=recipient_name,
                    current_location=current_location,
                    destination=destination,
                    status_history=[status_history]
                )
                delivery.save()
                return Response(delivery.to_dict(), status=201)
            except Exception:
                return Response({"error": "Failed to create delivery"}, status=500)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=401)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class DeliveryLocationUpdate(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def handle_exception(self, exc):
        if isinstance(exc, AuthenticationFailed):
            return Response({"error": str(exc)}, status=401)
        return super().handle_exception(exc)

    def put(self, request, delivery_id):
        try:
            location_input = request.data.get("location")
            location = validate_lat_lon_input(location_input)

            delivery = Delivery.objects(delivery_id=delivery_id).first()
            if not delivery:
                return Response({"error": "Delivery not found"}, status=404)

            delivery.current_location = location
            delivery.last_updated = datetime.now(timezone.utc)
            delivery.save()

            return Response({"message": "Location updated"}, status=200)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=401)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


class DeliveryStatusUpdate(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def handle_exception(self, exc):
        if isinstance(exc, AuthenticationFailed):
            return Response({"error": str(exc)}, status=401)
        return super().handle_exception(exc)

    def put(self, request, delivery_id):
        try:
            data = request.data
            status_value = data.get("status")
            location = data.get("location")

            if not status_value or not location:
                return Response({"error": "Missing status or location"}, status=400)

            if status_value not in VALID_STATUSES:
                return Response({"error": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"}, status=400)

            try:
                location = validate_lat_lon_input(location)
            except ValueError as e:
                return Response({"error": str(e)}, status=400)

            delivery = Delivery.objects(delivery_id=delivery_id).first()
            if not delivery:
                return Response({"error": "Delivery not found"}, status=404)

            try:
                status_history = StatusHistory(
                    status=status_value,
                    location=location
                )
            except Exception:
                return Response({"error": "Invalid status"}, status=400)

            delivery.status = status_value
            delivery.current_location = location
            delivery.last_updated = datetime.now(timezone.utc)
            delivery.status_history.append(status_history)
            delivery.save()

            # Send WebSocket update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"delivery_{delivery_id}",
                {
                    "type": "delivery_update",
                    "message": {
                        "status": status_value,
                        "location": location,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            )

            return Response({"message": "Status updated"}, status=200)
        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=401)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

def delivery_tracker(request, delivery_id):
    """
    Render the delivery tracking page.
    """
    delivery = Delivery.objects(delivery_id=delivery_id).first()
    if not delivery:
        return render(request, "deliveries/error.html", {"error": "Delivery not found"}, status=404)

    return render(request, "deliveries/tracker.html", {
        "delivery": delivery.to_dict(),
        "api_key": settings.MAPS_API_KEY
    })



