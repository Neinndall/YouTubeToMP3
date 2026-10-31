import os
import sys

# Asegurar que el directorio raíz de la aplicación esté en sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Agregar la carpeta tools al PATH
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
if os.path.exists(TOOLS_DIR) and TOOLS_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = TOOLS_DIR + os.pathsep + os.environ.get("PATH", "")

from gui import run_app

if __name__ == "__main__":
    run_app()
