import os
import subprocess
import sys
import shutil
from pathlib import Path

def check_chrome_installed():
    """Check if Chrome is installed"""
    chrome_paths = {
        "win32": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "linux": "/usr/bin/google-chrome"
    }
    
    platform = sys.platform
    chrome_path = chrome_paths.get(platform)
    
    if chrome_path and os.path.exists(chrome_path):
        print("✅ Google Chrome is installed.")
        return True
    else:
        print("❌ Google Chrome is not installed or not found in the default location.")
        print("Please install Google Chrome to use this bot.")
        return False

def create_virtual_environment():
    """Create a virtual environment"""
    print("Creating virtual environment...")
    
    if os.path.exists("venv"):
        print("Virtual environment already exists. Skipping creation.")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created.")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment.")
        return False

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("Installing dependencies...")
    
    venv_python = "venv/bin/python"
    if sys.platform == "win32":
        venv_python = r"venv\Scripts\python.exe"
    
    try:
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed.")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies.")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    print("Creating .env file...")
    
    if os.path.exists(".env"):
        print(".env file already exists. Skipping creation.")
        return True
    
    try:
        with open(".env", "w") as f:
            f.write("# MultiversX AI Twitter Bot Environment Variables\n\n")
            f.write("# Gemini AI API Key\n")
            f.write("GEMINI_API_KEY=your_gemini_api_key_here\n\n")
            f.write("# Twitter Credentials\n")
            f.write("TWITTER_USERNAME=your_twitter_username_or_email\n")
            f.write("TWITTER_PASSWORD=your_twitter_password\n")
        
        print("✅ .env file created. Please edit it with your API keys and credentials.")
        return True
    except:
        print("❌ Failed to create .env file.")
        return False

def main():
    """Main setup function"""
    print("Setting up MultiversX AI Twitter Bot...\n")
    
    # Check Chrome installation
    if not check_chrome_installed():
        return
    
    # Create virtual environment
    if not create_virtual_environment():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Create .env file
    if not create_env_file():
        return
    
    print("\n✅ Setup completed successfully!")
    print("\nTo run the bot:")
    if sys.platform == "win32":
        print("1. Activate the virtual environment: venv\\Scripts\\activate")
    else:
        print("1. Activate the virtual environment: source venv/bin/activate")
    print("2. Edit the .env file with your API keys and credentials")
    print("3. Run the bot: python src/main.py")

if __name__ == "__main__":
    main()