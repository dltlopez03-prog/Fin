# install_dependencies.py
import subprocess
import sys
from tqdm import tqdm
import time

# List of dependencies to install (added openai)
dependencies = [
    "openai",                        # ✅ Added
    "google-genai==1.7.0",
    "chromadb==0.6.3",
    "langgraph==0.3.21",
    "langchain-google-genai==2.1.2",
    "pandas",
    "matplotlib",
    "seaborn",
    "plotly",
    "ipywidgets",
    "python-dotenv",
    "tqdm",
    "scikit-learn",
]

def install_package(package: str):
    """Install a single package using pip"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-Uq", package])

def main():
    print("📦 Installing dependencies...\n")

    for package in tqdm(dependencies, desc="Installing", unit="pkg"):
        try:
            install_package(package)
        except subprocess.CalledProcessError:
            print(f"\n❌ Failed to install {package}. Please install it manually.")

        # Add a short delay so tqdm updates nicely
        time.sleep(0.1)

    print("\n✅ All dependencies installed successfully!")

if __name__ == "__main__":
    main()