"""
AI-Agent v4 - Setup Script
Automated virtual environment setup for cross-platform compatibility
Compatible with quick_start.bat
"""
import subprocess
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def run_command(command, shell=True):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def check_env_file(project_root):
    """Check and create .env file in backend directory"""
    backend_env = project_root / "backend" / ".env"
    
    if not backend_env.exists():
        print("\n⚠ Creating backend/.env file...")
        env_content = """# AI-Agent v4 - Environment Configuration
# LLM Provider Selection
GEMINI_ENABLED=false

# Gemini API Configuration (if GEMINI_ENABLED=true)
GEMINI_API_KEY=your_gemini_api_key_here

# Ollama Configuration (if GEMINI_ENABLED=false)
OLLAMA_HOST=http://localhost:11434

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
USE_SIMPLE_PROMPTS=true
FORCE_GPU=0

# Ollama Model Settings
OLLAMA_NUM_PREDICT_SCAMMER=200

# RAG System Configuration
RAG_COLLECTION_NAME=scam_cases
RAG_SIMILARITY_THRESHOLD=10.0
RAG_MAX_RESULTS=5

# Server Configuration
HOST=0.0.0.0
PORT=8000
"""
        backend_env.write_text(env_content, encoding='utf-8')
        print(f"[OK] Created {backend_env}")
        print("[WARNING] Please edit backend/.env to configure your settings")
        return False
    else:
        print(f"[OK] backend/.env exists")
        return True

def main():
    print("=" * 80)
    print("AI-Agent v4 - Environment Setup")
    print("Compatible with quick_start.bat")
    print("=" * 80)
    
    # Get project root
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    backend_path = project_root / "backend"
    
    # Step 1: Create virtual environment
    print("\n[1/6] Creating virtual environment...")
    if venv_path.exists():
        print(f"Virtual environment already exists at: {venv_path}")
        response = input("Do you want to recreate it? (y/n): ")
        if response.lower() == 'y':
            import shutil
            shutil.rmtree(venv_path)
            print("Removed existing virtual environment")
        else:
            print("Using existing virtual environment")
    
    if not venv_path.exists():
        if not run_command(f'"{sys.executable}" -m venv venv'):
            print("Failed to create virtual environment")
            return False
        print("[OK] Virtual environment created")
    
    # Step 2: Determine activation script
    print("\n[2/6] Detecting platform...")
    if sys.platform == "win32":
        activate_script = venv_path / "Scripts" / "activate"
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"
    
    print(f"Platform: {sys.platform}")
    print(f"Python: {python_executable}")
    print(f"Pip: {pip_executable}")
    
    # Step 3: Upgrade pip
    print("\n[3/6] Upgrading pip...")
    if not run_command(f'"{python_executable}" -m pip install --upgrade pip'):
        print("Warning: Failed to upgrade pip, continuing anyway...")
    else:
        print("[OK] Pip upgraded")
    
    # Step 4: Install dependencies
    print("\n[4/6] Installing dependencies...")
    requirements_file = backend_path / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Error: requirements.txt not found at {requirements_file}")
        return False
    
    print(f"Installing from: {requirements_file}")
    if not run_command(f'"{pip_executable}" install -r "{requirements_file}"'):
        print("Failed to install dependencies")
        return False
    
    print("[OK] Dependencies installed")
    
    # Step 5: Check environment configuration
    print("\n[5/6] Checking environment configuration...")
    env_exists = check_env_file(project_root)
    
    # Step 6: Check data files
    print("\n[6/6] Checking data files...")
    data_dir = project_root / "data"
    lite_data = data_dir / "scraped_alerts_lite.json"
    
    if not lite_data.exists():
        print("[WARNING] scraped_alerts_lite.json not found")
        print("  It will be created when you run quick_start.bat")
    else:
        print("[OK] scraped_alerts_lite.json exists")
    
    # Success message
    print("\n" + "=" * 80)
    print("[OK] Setup completed successfully!")
    print("=" * 80)
    
    # Next steps
    print("\n=== Next Steps ===")
    print("\n1. Configure your environment:")
    print("   Edit backend\\.env and set:")
    print("   - GEMINI_ENABLED=true (for Gemini API)")
    print("   - GEMINI_API_KEY=your_actual_key")
    print("   OR")
    print("   - GEMINI_ENABLED=false (for Ollama)")
    
    print("\n2. Start the application:")
    print("   Double-click: quick_start.bat")
    print("   OR manually:")
    if sys.platform == "win32":
        print("   .\\venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   cd backend")
    print("   python main.py")
    
    print("\n3. Access the services:")
    print("   Backend API:  http://localhost:8000")
    print("   API Docs:     http://localhost:8000/docs")
    print("   RPGv2:        http://localhost:3000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
