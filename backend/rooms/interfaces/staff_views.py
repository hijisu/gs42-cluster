"""운영팀 전용 회의실 API. 모든 뷰에 IsStaff를 적용한다."""

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from accounts.interfaces.decorators import staff_api
from rooms.application.staff_usecases import StaffBookingCommand
from rooms.interfaces import staff_deps as deps
from rooms.interfaces.serializers import room_payload, rules_payload
from rooms.interfaces.staff_serializers import (
    ReassignSerializer,
    RejectSerializer,
    RoomCreateSerializer,
    RoomPatchSerializer,
    RulesSerializer,
    StaffBookingSerializer,
    StaffListQuerySerializer,
    staff_reservation_payload,
)


@staff_api(["GET", "POST"])
def reservations(request):
    if request.method == "GET":
        query = StaffListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        views = deps.list_reservations().execute(
            query.validated_data.get("date"), query.validated_data.get("status")
        )
        return Response([staff_reservation_payload(v) for v in views])
    body = StaffBookingSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.book().execute(
            StaffBookingCommand(staff_id=request.user.pk, **body.validated_data)
        )
    return Response(staff_reservation_payload(view), status=status.HTTP_201_CREATED)


@staff_api(["POST"])
def approve(request, reservation_id: int):
    with transaction.atomic():
        view = deps.approve().execute(reservation_id)
    return Response(staff_reservation_payload(view))


@staff_api(["POST"])
def reject(request, reservation_id: int):
    body = RejectSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.reject().execute(reservation_id, body.validated_data["reason"])
    return Response(staff_reservation_payload(view))


@staff_api(["POST"])
def cancel(request, reservation_id: int):
    """운영팀 취소. 승인된 예약도 취소할 수 있다(교육생은 승인 전까지만)."""
    with transaction.atomic():
        view = deps.staff_cancel().execute(reservation_id)
    return Response(staff_reservation_payload(view))


@staff_api(["POST"])
def reassign(request, reservation_id: int):
    body = ReassignSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.reassign().execute(reservation_id, body.validated_data["room_id"])
    return Response(staff_reservation_payload(view))


@staff_api(["PUT"])
def rules(request):
    body = RulesSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    updated = deps.update_rules().execute(**body.validated_data)
    return Response(rules_payload(updated))


@staff_api(["POST"])
def create_room(request):
    body = RoomCreateSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    room = deps.create_room().execute(**body.validated_data)
    return Response(room_payload(room), status=status.HTTP_201_CREATED)


@staff_api(["PATCH"])
def update_room(request, room_id: int):
    body = RoomPatchSerializer(data=request.data, partial=True)
    body.is_valid(raise_exception=True)
    return Response(room_payload(deps.update_room().execute(room_id, dict(body.validated_data))))
