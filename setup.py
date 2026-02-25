"""Cross-platform setup script. Installs all dependencies for Quick-Seg."""
import subprocess
import sys


def main():
    print("Installing Quick-Seg dependencies...")
    print(f"Python: {sys.executable} ({sys.version})")
    print()

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
    except subprocess.CalledProcessError:
        print()
        print("ERROR: pip install failed. Try running manually:")
        print(f"  {sys.executable} -m pip install -r requirements.txt")
        sys.exit(1)

    print()
    print("Done. Run the app with:")
    print(f"  {sys.executable} app.py")


if __name__ == "__main__":
    main()
