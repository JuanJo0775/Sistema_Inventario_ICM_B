#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from datetime import datetime


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
    # --- AUTO-ACTIVACIÓN DE VENV ---
    # Si existe .venv y no lo estamos usando, re-ejecutar con el python del venv
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_exe = "Scripts\\python.exe" if os.name == "nt" else "bin/python"
    venv_python = os.path.join(base_dir, ".venv", venv_exe)

    if os.path.exists(venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_python).lower():
        import subprocess
        sys.exit(subprocess.call([venv_python] + sys.argv))
    # -------------------------------

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH env?"
        ) from exc
        
    if "runserver" in sys.argv and os.environ.get("RUN_MAIN") == "true":
        import django
        from django.db import connection
        from django.db.utils import OperationalError
        django.setup()
        try:
            connection.ensure_connection()
            print("\n" + "="*60)
            print("[OK] SERVIDOR ICM INICIADO CON EXITO")
            print("[OK] Conectado a la base de datos (PostgreSQL)")
            print("[INFO] Swagger UI : http://localhost:8000/api/docs/")
            print("[INFO] ReDoc      : http://localhost:8000/api/redoc/")
            print("="*60 + "\n")
        except OperationalError as e:
            print("\n" + "="*60)
            print("[ERROR] No se pudo conectar a la base de datos.")
            print("="*60 + "\n")

    if "runserver" in sys.argv:
        patch_runserver_message()

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
