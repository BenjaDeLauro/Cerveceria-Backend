"""Prepara la base al iniciar el servidor; permite otros comandos de Django."""

import os
import subprocess
import sys


def main():
    command = sys.argv[1:]
    if not command:
        raise SystemExit('Se necesita un comando para iniciar el contenedor.')

    if command[:3] == ['python', 'manage.py', 'runserver']:
        subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
        subprocess.run([sys.executable, 'manage.py', 'configurar_grupos'], check=True)

    os.execvp(command[0], command)


if __name__ == '__main__':
    main()
