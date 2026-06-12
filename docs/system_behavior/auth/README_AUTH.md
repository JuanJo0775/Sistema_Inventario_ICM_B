# Módulo de Autenticación

## 1. Resumen

El módulo `authentication` gestiona el ciclo de vida completo de usuarios, autenticación JWT, control de acceso por roles y horarios, y recuperación de contraseñas.

**RF-001** — Autenticación JWT (login, logout, refresh, cambio de contraseña, recuperación por email).
**RF-002** — Gestión de usuarios CRUD por almacenista.

---

## 2. Roles del sistema (BR-01)

| Rol | Código | Permiso DRF | Acceso |
|-----|--------|-------------|--------|
| Almacenista | `almacenista` | `IsAlmacenista` | Control total, 24/7 |
| Auxiliar de despacho | `auxiliar_despacho` | `IsAuxiliarDespacho` | Solo en franja horaria, con límites |
| Administrador | `administrador` | `IsAdministrador` | Solo lectura |

**BR-01**: Roles definidos en `User.role`. `almacenista` es el rol rector.
**BR-02**: Solo `almacenista` gestiona credenciales (crear, deshabilitar, cambiar rol).
**BR-03**: `auxiliar_despacho` solo opera 07:00-12:00 y 14:00-17:00 (America/Bogota).

---

## 3. Modelos

### 3.1 User

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `username` | CharField | Nombre de usuario |
| `email` | EmailField (unique) | Correo electrónico |
| `role` | CharField(32) | `almacenista` / `auxiliar_despacho` / `administrador` |
| `password` | CharField | Hash SHA-256 |
| `created_by` | FK -> User (nullable) | Almacenista que creó la cuenta |
| `phone` | CharField(20) | Teléfono de contacto |
| `is_active` | BooleanField | Cuenta habilitada/deshabilitada |
| `created_at` / `updated_at` | DateTimeField | Automáticos |

### 3.2 UserSchedule

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user` | OneToOneField -> User | Auxiliar |
| `morning_start` / `morning_end` | TimeField (nullable) | Franja mañana personalizada |
| `afternoon_start` / `afternoon_end` | TimeField (nullable) | Franja tarde personalizada |
| `is_active` | BooleanField | Schedule activo/inactivo |

Solo aplica a `auxiliar_despacho`. Si no hay schedule, se usan defaults del sistema.

### 3.3 TemporaryAccessPermit

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user` | FK -> User | Auxiliar |
| `start_datetime` / `end_datetime` | DateTimeField | Ventana de vigencia |
| `allow_24_7` | BooleanField | Acceso total en el periodo |
| `custom_morning_start/end` | TimeField (nullable) | Franja mañana custom |
| `custom_afternoon_start/end` | TimeField (nullable) | Franja tarde custom |
| `reason` | TextField | Motivo obligatorio |
| `granted_by` | FK -> User (nullable) | Almacenista que otorgó |
| `is_active` | BooleanField | Para revocación lógica |

### 3.4 PasswordResetToken

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user` | FK -> User | Usuario |
| `token_hash` | CharField(64, unique) | SHA-256 del raw token |
| `expires_at` | DateTimeField | Default 10 minutos |
| `used` / `used_at` | BooleanField / DateTimeField | Un solo uso |

---

## 4. Servicios

| Función | BR/RF | Descripción |
|---------|-------|-------------|
| `authenticate_user(username, password)` | RF-001, BR-03 | Autentica y valida horario auxiliar |
| `create_user(executor, data)` | RF-002, BR-02 | Crea usuario (solo almacenista) |
| `disable_user(executor, user_id)` | RF-002, BR-02 | Deshabilita + blacklist JWT |
| `enable_user(executor, user_id)` | RF-002 | Reactiva usuario |
| `update_user(executor, user_id, data)` | RF-002, BR-02 | Actualiza campos permitidos |
| `change_own_password(user, current, new)` | RF-001 | Self-service con verificación |
| `request_password_reset(email)` | RF-001 | Genera token SHA-256, email |
| `reset_password_with_token(token, new)` | RF-001 | Valida token y cambia password |
| `create_or_update_user_schedule(executor, user, data)` | BR-03 | Horario personalizado auxiliar |
| `grant_temporary_permit(executor, user, data)` | BR-03 | Permiso temporal fuera de horario |
| `revoke_temporary_permit(executor, permit_id)` | BR-03 | Revoca permiso |

---

## 5. Control de acceso horario (BR-03)

Tres niveles de evaluación para `auxiliar_despacho`:

```
1. TemporaryAccessPermit activo en rango de fechas
   → Si allow_24_7: acceso total
   → Si no: evalúa franjas custom del permiso
2. UserSchedule activo
   → Evalúa franjas personalizadas del schedule
3. Default del sistema
   → 07:00-12:00 y 14:00-17:00 (America/Bogota)
```

---

## 6. Endpoints

Todas las rutas bajo `/api/v1/auth/`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| POST | `login/` | AllowAny | Login JWT (username o email + password) |
| POST | `token/refresh/` | AllowAny | Renovar access token |
| POST | `logout/` | IsAuthenticated | Blacklist refresh token |
| GET | `me/` | IsAuthenticated | Perfil del usuario autenticado |
| GET/POST | `users/` | Almacenista | Listar / crear usuarios |
| GET/PUT/PATCH | `users/<pk>/` | Almacenista | Detalle / actualizar |
| POST | `users/<pk>/disable/` | Almacenista | Deshabilitar cuenta |
| POST | `users/<pk>/enable/` | Almacenista | Reactivar cuenta |
| GET/POST | `users/<pk>/schedule/` | Almacenista | Ver / configurar horario |
| GET/POST | `users/<pk>/temporary-permits/` | Almacenista | Listar / otorgar permisos |
| POST | `temporary-permits/<pk>/revoke/` | Almacenista | Revocar permiso |
| POST | `change-password/` | IsAuthenticated | Cambiar propia contraseña |
| POST | `forgot-password/` | AllowAny | Solicitar recuperación |
| POST | `reset-password/` | AllowAny | Reset con token |

---

## 7. Flujo de login

```
POST /auth/login/ { username|email, password }
  → authenticate_user()
    → authenticate() de Django
    → Si falla o inactivo: LOGIN_FAILED, error 401
    → Si auxiliar: check_user_access() — 3 niveles de horario
      → Fuera de horario: OutsideOperatingHoursError, 403
    → LOGIN_SUCCESS en audit log
    → Crea RefreshToken + AccessToken con claims: user_id, role
    → Retorna { access, refresh, user }
```

---

## 8. Escenarios esperados

**AUTH-S01**: Login almacenista exitoso → 200 + tokens + LOGIN_SUCCESS.
**AUTH-S02**: Login auxiliar fuera de horario → 403 + OutsideOperatingHoursError + LOGIN_FAILED.
**AUTH-S03**: Login auxiliar con permiso temporal 24/7 → acceso permitido fuera de franja.
**AUTH-S04**: Crear usuario por almacenista → 201 + USER_CREATED.
**AUTH-S05**: Deshabilitar usuario → is_active=False, JWT blacklist, USER_DISABLED.
**AUTH-S06**: Reset password con token expirado → 422 DomainValidationError.
**AUTH-S07**: Auxiliar intenta crear usuario → 403 UnauthorizedCredentialManagementError.
