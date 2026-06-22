"""
OWASP Top 10 security tests — Sistema Inventario ICM.

Verifica controles de seguridad en tiempo de ejecución para las categorías
OWASP Top 10 más relevantes en una API REST Django:

  A01 — Broken Access Control
  A02 — Cryptographic Failures
  A03 — Injection
  A05 — Security Misconfiguration
  A07 — Identification and Authentication Failures

Estos tests complementan el SAST estático (semgrep, bandit) con verificación
dinámica del comportamiento HTTP real de la API.
"""
from __future__ import annotations

import base64
import json

import pytest
from django.urls import reverse


# ── A01 — Broken Access Control ──────────────────────────────────────────────
# RF-001, RF-002, BR-01, BR-02


@pytest.mark.django_db
class TestA01BrokenAccessControl:
    """Recursos protegidos requieren autenticación y autorización por rol."""

    # Endpoints que deben devolver 401 sin token
    _REQUIRES_AUTH = [
        ("GET", "inventory-full"),
        ("GET", "movements-list"),
        ("GET", "audit-logs"),
        ("GET", "catalog-categories"),
        ("GET", "auth-me"),
        ("GET", "reports-kpi"),
    ]

    @pytest.mark.parametrize("method,url_name", _REQUIRES_AUTH)
    def test_unauthenticated_request_returns_401(self, api_client, method, url_name):
        url = reverse(url_name)
        r = getattr(api_client, method.lower())(url)
        assert r.status_code == 401, (
            f"{method} {url_name} debe requerir autenticación (obtuvo {r.status_code})"
        )

    def test_auxiliar_cannot_list_users(self, api_client, auxiliar_user):
        """RF-002 — Solo almacenista puede gestionar usuarios; auxiliar → 403."""
        api_client.force_authenticate(user=auxiliar_user)
        r = api_client.get(reverse("auth-users"))
        assert r.status_code == 403

    def test_auxiliar_cannot_disable_another_user(
        self, api_client, auxiliar_user, almacenista_user
    ):
        """RF-002 — Auxiliar no puede deshabilitar a otro usuario (IDOR + escalada de rol)."""
        api_client.force_authenticate(user=auxiliar_user)
        r = api_client.post(
            reverse("auth-user-disable", kwargs={"pk": almacenista_user.pk})
        )
        assert r.status_code == 403

    def test_auxiliar_cannot_access_audit_logs(self, api_client, auxiliar_user):
        """Auxiliar no tiene acceso a los logs de auditoría (solo almacenista/administrador)."""
        api_client.force_authenticate(user=auxiliar_user)
        r = api_client.get(reverse("audit-logs"))
        assert r.status_code == 403

    def test_administrador_cannot_post_catalog_product(
        self, api_client, administrador_user
    ):
        """RF-002 — Administrador es solo lectura; no puede crear productos → 403."""
        api_client.force_authenticate(user=administrador_user)
        r = api_client.post(
            reverse("catalog-products"),
            {"sku": "SEC-0001", "name": "Test", "category_id": "00000000-0000-0000-0000-000000000001"},
            format="json",
        )
        assert r.status_code == 403

    def test_administrador_cannot_post_entry(self, api_client, administrador_user):
        """Administrador no puede registrar entradas de inventario → 403."""
        api_client.force_authenticate(user=administrador_user)
        r = api_client.post(
            reverse("movements-entries"),
            {
                "product_id": "00000000-0000-0000-0000-000000000001",
                "location_id": "00000000-0000-0000-0000-000000000002",
                "quantity": 1,
            },
            format="json",
        )
        assert r.status_code == 403

    def test_idor_auxiliar_cannot_read_other_user_detail(
        self, api_client, auxiliar_user, almacenista_user
    ):
        """IDOR — Auxiliar no puede leer el perfil de otro usuario por UUID."""
        api_client.force_authenticate(user=auxiliar_user)
        r = api_client.get(
            reverse("auth-user-detail", kwargs={"pk": almacenista_user.pk})
        )
        # El endpoint es solo para almacenista; auxiliar debe recibir 403 o 404
        assert r.status_code in (403, 404)

    def test_idor_unauthenticated_movement_detail_returns_401(
        self, api_client, almacenista_user, sample_product, sample_locations
    ):
        """IDOR — Un movimiento no puede ser accedido sin autenticación."""
        from apps.movements.services import register_entry

        movement = register_entry(
            almacenista_user,
            sample_product.id,
            sample_locations[0].id,
            3,
            cold_chain_acknowledged=True,
            electrical_safety_acknowledged=True,
        )
        r = api_client.get(
            reverse("movements-detail", kwargs={"pk": movement.pk})
        )
        assert r.status_code == 401

    def test_unauthenticated_post_entry_returns_401(self, api_client):
        """POST a entry endpoint sin token devuelve 401, no 400."""
        r = api_client.post(
            reverse("movements-entries"),
            {"product_id": "x", "quantity": 1},
            format="json",
        )
        assert r.status_code == 401


# ── A02 — Cryptographic Failures ─────────────────────────────────────────────


@pytest.mark.django_db
class TestA02CryptographicFailures:
    """Datos sensibles no se exponen en respuestas; tokens JWT tienen expiración."""

    def test_login_response_does_not_expose_password(self, api_client, almacenista_user):
        """El campo password nunca aparece en la respuesta de login."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": almacenista_user.username, "password": "testpass123"},
            format="json",
        )
        assert r.status_code == 200
        body = r.json()
        assert "password" not in body
        user_data = body.get("user", {})
        assert "password" not in user_data

    def test_me_endpoint_does_not_expose_password(
        self, api_client, almacenista_user
    ):
        """El endpoint /me/ no devuelve el hash de la contraseña."""
        api_client.force_authenticate(user=almacenista_user)
        r = api_client.get(reverse("auth-me"))
        assert r.status_code == 200
        body = r.json()
        assert "password" not in body

    def test_access_token_has_expiry_claim(self, api_client, almacenista_user):
        """El JWT de acceso debe contener un claim `exp` (expiración)."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": almacenista_user.username, "password": "testpass123"},
            format="json",
        )
        assert r.status_code == 200
        access = r.json()["access"]
        # Decodificar payload sin verificar firma (solo comprobar estructura)
        padding = "=" * (-len(access.split(".")[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(access.split(".")[1] + padding))
        assert "exp" in payload, "El token de acceso debe tener claim 'exp'"
        assert payload["exp"] > 0

    def test_user_list_does_not_expose_password(self, api_client, almacenista_user):
        """La lista de usuarios no devuelve hashes de contraseña."""
        api_client.force_authenticate(user=almacenista_user)
        r = api_client.get(reverse("auth-users"))
        assert r.status_code == 200
        results = r.json().get("results", r.json()) if isinstance(r.json(), dict) else r.json()
        if isinstance(results, list):
            for user in results:
                assert "password" not in user


# ── A03 — Injection ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestA03Injection:
    """Patrones de inyección no causan errores 5xx — el ORM y la validación los absorben."""

    _SQL_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT * FROM auth_user--",
        "admin'--",
    ]

    @pytest.mark.parametrize("payload", _SQL_PAYLOADS)
    def test_sql_injection_in_login_username_does_not_cause_500(
        self, api_client, payload
    ):
        """SQL injection en username de login → 400 o 401, nunca 500."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": payload, "password": "wrong"},
            format="json",
        )
        assert r.status_code in (400, 401), (
            f"Payload SQL en username produjo {r.status_code}, esperado 400/401"
        )

    @pytest.mark.parametrize("payload", _SQL_PAYLOADS)
    def test_sql_injection_in_login_password_does_not_cause_500(
        self, api_client, almacenista_user, payload
    ):
        """SQL injection en password → 400 o 401, nunca 500."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": almacenista_user.username, "password": payload},
            format="json",
        )
        assert r.status_code in (400, 401)

    @pytest.mark.parametrize("payload", _SQL_PAYLOADS)
    def test_sql_injection_in_search_query_does_not_cause_500(
        self, api_client, almacenista_user, payload
    ):
        """SQL injection en parámetro de búsqueda → 200 o 400, nunca 500."""
        api_client.force_authenticate(user=almacenista_user)
        r = api_client.get(reverse("inventory-search"), {"q": payload})
        assert r.status_code in (200, 400), (
            f"Payload SQL en búsqueda produjo {r.status_code}"
        )

    def test_xss_payload_in_search_returns_json_not_html(
        self, api_client, almacenista_user
    ):
        """XSS en parámetro de búsqueda: la respuesta es JSON, no HTML sin escapar."""
        api_client.force_authenticate(user=almacenista_user)
        r = api_client.get(
            reverse("inventory-search"),
            {"q": "<script>alert('xss')</script>"},
        )
        assert r.status_code in (200, 400)
        assert r.get("Content-Type", "").startswith("application/json")
        assert "<script>" not in r.content.decode("utf-8", errors="replace")


# ── A05 — Security Misconfiguration ──────────────────────────────────────────


@pytest.mark.django_db
class TestA05SecurityMisconfiguration:
    """Configuración segura: rutas inexistentes y accesos no autorizados bien manejados."""

    def test_nonexistent_api_path_returns_404(self, api_client):
        """Rutas desconocidas bajo /api/ devuelven 404, no 200 ni 500."""
        r = api_client.get("/api/v1/nonexistent-endpoint-xyz/")
        assert r.status_code == 404

    def test_health_endpoint_is_public(self, api_client):
        """El endpoint de health check es público y responde 200 sin token."""
        r = api_client.get(reverse("auth-health"))
        assert r.status_code == 200

    def test_api_endpoint_error_uses_json_content_type(
        self, api_client, almacenista_user
    ):
        """Los errores de validación en endpoints reales devuelven JSON, no HTML."""
        api_client.force_authenticate(user=almacenista_user)
        # POST sin body a un endpoint que valida → 400 con Content-Type JSON
        r = api_client.post(reverse("movements-entries"), {}, format="json")
        assert r.status_code == 400
        ct = r.get("Content-Type", "")
        assert "json" in ct, f"Content-Type inesperado en respuesta 400: {ct}"

    def test_schema_endpoint_accessible_in_test_mode(self, api_client):
        """El schema OpenAPI es accesible (RESTRICT_API_SCHEMA=False en test)."""
        r = api_client.get("/api/schema/")
        # En test RESTRICT_API_SCHEMA=False → cualquier usuario puede verlo
        assert r.status_code in (200, 404)  # 404 si spectacular no está montado

    def test_no_server_error_on_malformed_json_body(
        self, api_client, almacenista_user
    ):
        """JSON malformado en body de POST no produce 500 (DRF lo rechaza con 400)."""
        api_client.force_authenticate(user=almacenista_user)
        r = api_client.post(
            reverse("movements-entries"),
            data="this is not json{{",
            content_type="application/json",
        )
        assert r.status_code in (400, 415), (
            f"JSON malformado produjo {r.status_code}, esperado 400 o 415"
        )


# ── A07 — Identification and Authentication Failures ─────────────────────────


@pytest.mark.django_db
class TestA07AuthenticationFailures:
    """Controles de autenticación: credenciales incorrectas, tokens inválidos y expirados."""

    def test_wrong_password_returns_401(self, api_client, almacenista_user):
        """Contraseña incorrecta → 401, nunca 200 ni 403."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": almacenista_user.username, "password": "wrong_password_xyz"},
            format="json",
        )
        assert r.status_code == 401

    def test_nonexistent_user_returns_401(self, api_client):
        """Usuario inexistente → 401, no revela si el usuario existe (no 404)."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "nonexistent_user_xyz_123", "password": "any_password"},
            format="json",
        )
        assert r.status_code == 401

    def test_empty_credentials_returns_400(self, api_client):
        """Credenciales vacías → 400 (validación), no 401."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {},
            format="json",
        )
        assert r.status_code == 400

    def test_tampered_jwt_returns_401(self, api_client, almacenista_user):
        """JWT con firma alterada → 401."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": almacenista_user.username, "password": "testpass123"},
            format="json",
        )
        assert r.status_code == 200
        token = r.json()["access"]
        # Alterar el último segmento (firma)
        tampered = token[:-10] + "AAAAAAAAAA"
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered}")
        r2 = api_client.get(reverse("auth-me"))
        assert r2.status_code == 401

    def test_random_string_as_bearer_token_returns_401(self, api_client):
        """String arbitrario como Bearer token → 401."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer totally_invalid_token_xyz")
        r = api_client.get(reverse("inventory-full"))
        assert r.status_code == 401

    def test_empty_bearer_token_returns_401(self, api_client):
        """Bearer vacío → 401."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer ")
        r = api_client.get(reverse("inventory-full"))
        assert r.status_code == 401

    def test_missing_authorization_header_returns_401(self, api_client):
        """Sin header Authorization → 401."""
        r = api_client.get(reverse("auth-me"))
        assert r.status_code == 401

    def test_refresh_token_cannot_access_protected_endpoints(
        self, api_client, almacenista_user
    ):
        """El refresh token no es válido como access token en endpoints protegidos."""
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": almacenista_user.username, "password": "testpass123"},
            format="json",
        )
        assert r.status_code == 200
        refresh_token = r.json()["refresh"]
        # Usar refresh token donde se espera access token
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh_token}")
        r2 = api_client.get(reverse("auth-me"))
        assert r2.status_code == 401

    def test_inactive_user_cannot_authenticate(self, api_client, auxiliar_user):
        """Usuario desactivado (is_active=False) no puede obtener tokens."""
        auxiliar_user.is_active = False
        auxiliar_user.save()
        r = api_client.post(
            reverse("token_obtain_pair"),
            {"username": auxiliar_user.username, "password": "testpass123"},
            format="json",
        )
        assert r.status_code in (400, 401)
