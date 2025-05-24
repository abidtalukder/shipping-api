from django.urls import path
from deliveries.views import (
    DeliveryDetailView,
    MyDeliveriesView,
    DeliveryListCreate,
    DeliveryLocationUpdate,
    DeliveryStatusUpdate,
    delivery_tracker
)

urlpatterns = [
    # Admin routes
    path('', DeliveryListCreate.as_view(), name='delivery_list_create'),
    path('<str:delivery_id>/location/', DeliveryLocationUpdate.as_view(), name='delivery_location_update'),
    path('<str:delivery_id>/status/', DeliveryStatusUpdate.as_view(), name='delivery_status_update'),

    # User routes
    path('my/', MyDeliveriesView.as_view(), name='my_deliveries'),

    # Public routes
    path('<str:delivery_id>/', DeliveryDetailView.as_view(), name='delivery_detail'),
    path('track/<str:delivery_id>/', delivery_tracker, name='delivery_tracker'),
] 