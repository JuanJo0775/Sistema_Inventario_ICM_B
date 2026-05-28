#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from datetime import datetime


def run_system_health_check():
    """
    Realiza un diagnóstico real del sistema antes de arrancar el servidor.
    Verifica DB (PostgreSQL), migraciones pendientes y entorno.
    """
    from django.conf import settings
    from django.db import connection
    from django.db.utils import OperationalError
    from django.core.management import call_command
    from django.core.management.color import color_style
    from io import StringIO

    style = color_style()

    print("\n" + "-" * 60)
    print(style.MIGRATE_LABEL("SISTEMA DE INVENTARIO ICM - DIAGNÓSTICO DE ARRANQUE"))
    print("-" * 60)

    # 1. Conexion Real a Base de Datos (PostgreSQL)
    try:
        connection.ensure_connection()
        # Verificacion extra: ejecutar una consulta real
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        db_info = settings.DATABASES["default"]
        engine = db_info["ENGINE"].split(".")[-1]
        db_name = db_info["NAME"]
        host = db_info.get("HOST", "localhost")

        print(
            f"{style.SUCCESS('[OK]')} Base de Datos ({engine}) : CONECTADA [{db_name} en {host}]"
        )
    except OperationalError as e:
        print(f"{style.ERROR('[ERROR]')} Base de Datos : NO SE PUDO CONECTAR")
        print(f"        Detalle: {e}")
    except Exception as e:
        print(f"{style.ERROR('[ERROR]')} Base de Datos : ERROR INESPERADO")
        print(f"        Detalle: {e}")

    # 2. Migraciones Pendientes
    try:
        out = StringIO()
        call_command("showmigrations", format="plan", stdout=out)
        out.seek(0)
        pending = [line for line in out.readlines() if "[ ]" in line]

        if pending:
            print(
                f"{style.WARNING('[ALERTA]')} Migraciones : {len(pending)} PENDIENTES (Ejecute 'python manage.py migrate')"
            )
        else:
            print(f"{style.SUCCESS('[OK]')} Migraciones : AL DIA")
    except Exception:
        print(f"{style.NOTICE('[INFO]')} Migraciones : ESTADO DESCONOCIDO")

    # 3. Entorno y Debug
    env = "DESARROLLO" if settings.DEBUG else "PRODUCCION"
    status_msg = "DEBUG ACTIVADO" if settings.DEBUG else "MODO PRODUCCION"
    print(f"{style.NOTICE('[INFO]')} Entorno : {env} ({status_msg})")

    # 4. Accesos Rapidos
    print("-" * 60)
    print(f"Swagger UI : http://localhost:8000/api/docs/")
    print(f"ReDoc      : http://localhost:8000/api/redoc/")
    print("-" * 60 + "\n")


def patch_runserver_message():
    """Cambia el mensaje de 'CTRL-BREAK' por 'CTRL+C' en Windows."""
    try:
        from django.core.management.commands import runserver

        def custom_on_bind(self, server_port):
            quit_command = "CTRL+C"
            if self._raw_ipv6:
                addr = f"[{self.addr}]"
            elif self.addr == "0":
                addr = "0.0.0.0"
            else:
                addr = self.addr
            now = datetime.now().strftime("%B %d, %Y - %X")
            version = self.get_version()
            from django.conf import settings

            print(
                f"{now}\n"
                f"Django version {version}, using settings {settings.SETTINGS_MODULE!r}\n"
                f"Starting development server at {self.protocol}://{addr}:{server_port}/\n"
                f"Quit the server with {quit_command}.",
                file=self.stdout,
            )

        runserver.Command.on_bind = custom_on_bind
    except Exception:
        pass


def main():
    # --- AUTO-ACTIVACION DE VENV ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_exe = "Scripts\\python.exe" if os.name == "nt" else "bin/python"
    venv_python = os.path.join(base_dir, ".venv", venv_exe)

    if (
        os.path.exists(venv_python)
        and os.path.abspath(sys.executable).lower()
        != os.path.abspath(venv_python).lower()
    ):
        import subprocess

        try:
            sys.exit(subprocess.call([venv_python] + sys.argv))
        except KeyboardInterrupt:
            sys.exit(0)
    # -------------------------------

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH env?"
        ) from exc

    if "runserver" in sys.argv and os.environ.get("RUN_MAIN") == "true":
        import django

        django.setup()
        run_system_health_check()

    if "runserver" in sys.argv:
        patch_runserver_message()

    try:
        execute_from_command_line(sys.argv)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
