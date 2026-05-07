import os
import subprocess


def revert():
    print("Iniciando restauración total desde GitHub...")
    try:
        # Intentamos resetear al último estado de la rama principal
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        print("✅ ¡Restauración exitosa! Tu sistema ha vuelto a su estado original.")
    except Exception as e:
        try:
            # Reintento con master por si acaso
            subprocess.run(["git", "reset", "--hard", "origin/master"], check=True)
            print("✅ ¡Restauración exitosa (rama master)! Tu sistema ha vuelto a su estado original.")
        except:
            print(f"❌ Error al restaurar: {e}")
            print("Por favor, ejecuta manualmente: git reset --hard origin/main")


if __name__ == "__main__":
    revert()
