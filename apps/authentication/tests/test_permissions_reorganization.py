from datetime import datetime, time, timedelta

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.audit.models import AuditEventType, AuditLog
from apps.authentication.models import TemporaryAccessPermit, UserRole, UserSchedule
from apps.authentication.selectors import check_user_access
from apps.authentication.services import (
    create_or_update_user_schedule,
    grant_temporary_permit,
    revoke_temporary_permit,
)
from tests.factories import UserFactory


@pytest.mark.django_db
class TestPermissionsReorganization:

    def test_default_operating_hours(self, auxiliar_user):
        # We test default operating hours (07:00-12:00, 14:00-17:00)
        # Using check_user_access directly
        tz = timezone.get_current_timezone()

        # Within morning range (08:00)
        dt_morning = timezone.make_aware(
            datetime.combine(datetime.today(), time(8, 0)), tz
        )
        assert check_user_access(auxiliar_user, dt_morning) is True

        # Outside range (13:00)
        dt_middle = timezone.make_aware(
            datetime.combine(datetime.today(), time(13, 0)), tz
        )
        assert check_user_access(auxiliar_user, dt_middle) is False

        # Non-auxiliar users are unrestricted
        almacenista = UserFactory(role=UserRole.ALMACENISTA)
        assert check_user_access(almacenista, dt_middle) is True

    def test_user_schedule_overrides_default(self, auxiliar_user):
        tz = timezone.get_current_timezone()
        # Custom schedule: morning 09:00 - 11:00
        schedule = UserSchedule.objects.create(
            user=auxiliar_user,
            morning_start=time(9, 0),
            morning_end=time(11, 0),
            is_active=True,
        )

        # 08:00 was allowed by default, now it should be blocked because custom schedule overrides it
        dt_08 = timezone.make_aware(datetime.combine(datetime.today(), time(8, 0)), tz)
        assert check_user_access(auxiliar_user, dt_08) is False

        # 09:30 is within custom morning range
        dt_0930 = timezone.make_aware(
            datetime.combine(datetime.today(), time(9, 30)), tz
        )
        assert check_user_access(auxiliar_user, dt_0930) is True

    def test_empty_user_schedule_blocks_all(self, auxiliar_user):
        tz = timezone.get_current_timezone()
        # Custom schedule with no hours defined
        UserSchedule.objects.create(user=auxiliar_user, is_active=True)

        # 08:00 (which was allowed by default) is now blocked
        dt_08 = timezone.make_aware(datetime.combine(datetime.today(), time(8, 0)), tz)
        assert check_user_access(auxiliar_user, dt_08) is False

    def test_temporary_permit_allow_24_7(self, almacenista_user, auxiliar_user):
        tz = timezone.get_current_timezone()
        start = timezone.now() - timedelta(hours=1)
        end = timezone.now() + timedelta(hours=1)

        permit = grant_temporary_permit(
            almacenista_user,
            auxiliar_user,
            {
                "start_datetime": start,
                "end_datetime": end,
                "allow_24_7": True,
                "reason": "Midnight inventory",
            },
        )

        assert permit.is_active is True
        # Current time (which is between start and end) should be allowed even if it is a dead hour
        assert check_user_access(auxiliar_user, timezone.now()) is True

    def test_overlapping_permits_union(self, almacenista_user, auxiliar_user):
        tz = timezone.get_current_timezone()
        # Create two overlapping permits for the same range:
        # Permit 1: 01:00 - 03:00 (morning custom range)
        # Permit 2: 02:30 - 05:00 (morning custom range)
        base_date = datetime.today()
        start = timezone.make_aware(datetime.combine(base_date, time(0, 0)), tz)
        end = timezone.make_aware(datetime.combine(base_date, time(6, 0)), tz)

        grant_temporary_permit(
            almacenista_user,
            auxiliar_user,
            {
                "start_datetime": start,
                "end_datetime": end,
                "custom_morning_start": time(1, 0),
                "custom_morning_end": time(3, 0),
                "reason": "First shift",
            },
        )

        grant_temporary_permit(
            almacenista_user,
            auxiliar_user,
            {
                "start_datetime": start,
                "end_datetime": end,
                "custom_morning_start": time(2, 30),
                "custom_morning_end": time(5, 0),
                "reason": "Second shift overlap",
            },
        )

        # 02:00: Allowed by Permit 1
        dt_02 = timezone.make_aware(datetime.combine(base_date, time(2, 0)), tz)
        assert check_user_access(auxiliar_user, dt_02) is True

        # 04:00: Allowed by Permit 2
        dt_04 = timezone.make_aware(datetime.combine(base_date, time(4, 0)), tz)
        assert check_user_access(auxiliar_user, dt_04) is True

        # 05:30: Outside both custom ranges (but within the permit date range) -> blocked
        dt_0530 = timezone.make_aware(datetime.combine(base_date, time(5, 30)), tz)
        assert check_user_access(auxiliar_user, dt_0530) is False

    def test_model_validations(self, auxiliar_user):
        # Time validations: morning_start >= morning_end raises validation error
        with pytest.raises(DjangoValidationError):
            UserSchedule.objects.create(
                user=auxiliar_user, morning_start=time(10, 0), morning_end=time(9, 0)
            )

        # TemporaryPermit validation: allow_24_7=False but no custom ranges raises validation error
        with pytest.raises(DjangoValidationError):
            TemporaryAccessPermit.objects.create(
                user=auxiliar_user,
                start_datetime=timezone.now(),
                end_datetime=timezone.now() + timedelta(hours=1),
                allow_24_7=False,
                reason="Invalid",
            )

    def test_almacenista_delegation_limits(self, almacenista_user, auxiliar_user):
        other_almacenista = UserFactory(role=UserRole.ALMACENISTA)

        # Almacenista cannot modify their own schedule or other almacenistas
        from shared.exceptions import DomainValidationError

        with pytest.raises(DomainValidationError):
            create_or_update_user_schedule(
                almacenista_user,
                almacenista_user,
                {"morning_start": time(9, 0), "morning_end": time(10, 0)},
            )

        with pytest.raises(DomainValidationError):
            create_or_update_user_schedule(
                almacenista_user,
                other_almacenista,
                {"morning_start": time(9, 0), "morning_end": time(10, 0)},
            )

    def test_enriched_audit_logs(self, almacenista_user, auxiliar_user):
        # Grant temporary permit
        start = timezone.now()
        end = timezone.now() + timedelta(hours=2)
        permit = grant_temporary_permit(
            almacenista_user,
            auxiliar_user,
            {
                "start_datetime": start,
                "end_datetime": end,
                "allow_24_7": True,
                "reason": "Audited shift",
            },
        )

        audit_log = AuditLog.objects.filter(
            event_type=AuditEventType.PERMISSION_CHANGED, user=almacenista_user
        ).first()

        assert audit_log is not None
        assert audit_log.metadata["change_type"] == "permit_granted"
        assert audit_log.metadata["target_user"]["username"] == auxiliar_user.username
        assert audit_log.metadata["new_values"]["reason"] == "Audited shift"

        # Revoke permit
        revoke_temporary_permit(almacenista_user, permit.id)

        revoked_log = (
            AuditLog.objects.filter(
                event_type=AuditEventType.PERMISSION_CHANGED, user=almacenista_user
            )
            .order_by("-created_at")
            .first()
        )

        assert revoked_log is not None
        assert revoked_log.metadata["change_type"] == "permit_revoked"
        assert revoked_log.metadata["permit_id"] == str(permit.id)

    def test_request_level_cache(self, auxiliar_user):
        # Since check_user_access stores result on user instance,
        # consecutive calls for the same dt should not run DB queries.
        # We can verify by patching the db call or simply checking that it is set.
        tz = timezone.get_current_timezone()
        dt = timezone.make_aware(datetime.combine(datetime.today(), time(8, 0)), tz)

        # Clean potential cache first
        cache_attr = f"_cached_access_allowed_{dt.astimezone(tz).isoformat()[:16]}"
        if hasattr(auxiliar_user, cache_attr):
            delattr(auxiliar_user, cache_attr)

        allowed = check_user_access(auxiliar_user, dt)
        assert allowed is True
        assert getattr(auxiliar_user, cache_attr) is True

        # Manually alter the cache on the object and verify check_user_access returns the cached value
        setattr(auxiliar_user, cache_attr, False)
        assert check_user_access(auxiliar_user, dt) is False
