from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from rooms.application.usecases import RequestReservationCommand
from rooms.interfaces import deps
from rooms.interfaces.serializers import (
    AvailabilityQuerySerializer,
    ReservationRequestSerializer,
    availability_payload,
    reservation_payload,
    room_payload,
    rules_payload,
)


@api_view(["GET"])
def list_rooms(request):
    return Response([room_payload(r) for r in deps.list_rooms().execute()])


@api_view(["GET"])
def rules(request):
    return Response(rules_payload(deps.get_rules().execute()))


@api_view(["GET"])
def availability(request):
    query = AvailabilityQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    day = query.validated_data["date"]
    items = deps.get_availability().execute(day, viewer_id=request.user.pk)
    return Response(availability_payload(day, items))


@api_view(["POST"])
def create_reservation(request):
    body = ReservationRequestSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.request_reservation().execute(
            RequestReservationCommand(user_id=request.user.pk, **body.validated_data)
        )
    return Response(reservation_payload(view), status=status.HTTP_201_CREATED)


@api_view(["GET"])
def my_reservations(request):
    views = deps.list_my_reservations().execute(request.user.pk)
    return Response([reservation_payload(v) for v in views])


@api_view(["POST"])
def cancel(request, reservation_id: int):
    with transaction.atomic():
        view = deps.cancel_reservation().execute(reservation_id, request.user.pk)
    return Response(reservation_payload(view))
