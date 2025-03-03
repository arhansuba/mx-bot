#!/usr/bin/env python3
import os
import sys
import time
import shutil
import argparse
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deploy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("deploy")

class DeploymentManager:
    def __init__(self, args):
        self.args = args
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.src_dir = os.path.join(self.project_root, "src")
        self.data_dir = os.path.join(self.project_root, "data")
        self.env_file = os.path.join(self.project_root, ".env")
        self.venv_dir = os.path.join(self.project_root, "venv")
        self.backup_dir = os.path.join(self.project_root, "backups")
        self.service_name = "multiversx-ai-bot"
        
        # Detect OS
        self.is_windows = sys.platform.startswith('win')
        self.is_linux = sys.platform.startswith('linux')
        self.is_macos = sys.platform.startswith('darwin')
        
        # Python commands
        self.python_cmd = os.path.join(self.venv_dir, "Scripts", "python.exe") if self.is_windows else os.path.join(self.venv_dir, "bin", "python")
        self.pip_cmd = os.path.join(self.venv_dir, "Scripts", "pip.exe") if self.is_windows else os.path.join(self.venv_dir, "bin", "pip")
        
        # Create directories if needed
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def run_command(self, cmd, cwd=None, check=True, shell=False):
        """Run a shell command"""
        logger.info(f"Running command: {cmd}")
        try:
            if shell:
                result = subprocess.run(cmd, shell=True, check=check, cwd=cwd, text=True, capture_output=True)
            else:
                result = subprocess.run(cmd, check=check, cwd=cwd, text=True, capture_output=True)
            
            if result.stdout:
                logger.debug(result.stdout)
            
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            logger.error(f"Output: {e.output}")
            if not check:
                return e
            raise
    
    def create_virtual_environment(self):
        """Create a virtual environment"""
        if os.path.exists(self.venv_dir):
            if self.args.force:
                logger.info("Removing existing virtual environment")
                shutil.rmtree(self.venv_dir)
            else:
                logger.info("Virtual environment already exists, skipping creation")
                return
        
        logger.info("Creating virtual environment")
        self.run_command([sys.executable, "-m", "venv", self.venv_dir])
    
    def install_dependencies(self):
        """Install required dependencies"""
        logger.info("Installing dependencies")
        self.run_command([self.pip_cmd, "install", "--upgrade", "pip"])
        self.run_command([self.pip_cmd, "install", "-r", "requirements.txt"])
        
        # Install MultiversX SDK if requested
        if self.args.with_sdk:
            logger.info("Installing MultiversX SDK")
            self.run_command([self.pip_cmd, "install", "multiversx-sdk"])
    
    def backup_data(self):
        """Create a backup of data directory"""
        if not os.path.exists(self.data_dir) or not os.listdir(self.data_dir):
            logger.info("No data to backup")
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"data_backup_{timestamp}")
        
        logger.info(f"Creating backup at {backup_path}")
        shutil.copytree(self.data_dir, backup_path)
    
    def configure_environment(self):
        """Create or update the environment file"""
        if os.path.exists(self.env_file) and not self.args.force:
            logger.info(".env file already exists, skipping configuration")
            return
        
        logger.info("Configuring environment")
        
        # Create base .env file if it doesn't exist
        if not os.path.exists(self.env_file):
            with open(self.env_file, "w") as f:
                f.write("# MultiversX AI Twitter Bot Environment Variables\n\n")
                f.write("# Gemini AI API Key\n")
                f.write("GEMINI_API_KEY=\n\n")
                f.write("# Twitter Credentials\n")
                f.write("TWITTER_USERNAME=\n")
                f.write("TWITTER_PASSWORD=\n")
        
        # Prompt for values if needed
        if self.args.interactive:
            env_vars = {}
            
            with open(self.env_file, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value
            
            # Prompt for missing values
            if not env_vars.get("GEMINI_API_KEY"):
                env_vars["GEMINI_API_KEY"] = input("Enter Gemini AI API Key: ")
            
            if not env_vars.get("TWITTER_USERNAME"):
                env_vars["TWITTER_USERNAME"] = input("Enter Twitter Username: ")
            
            if not env_vars.get("TWITTER_PASSWORD"):
                env_vars["TWITTER_PASSWORD"] = input("Enter Twitter Password: ")
            
            # Write updated values
            with open(self.env_file, "w") as f:
                f.write("# MultiversX AI Twitter Bot Environment Variables\n\n")
                f.write("# Gemini AI API Key\n")
                f.write(f"GEMINI_API_KEY={env_vars.get('GEMINI_API_KEY', '')}\n\n")
                f.write("# Twitter Credentials\n")
                f.write(f"TWITTER_USERNAME={env_vars.get('TWITTER_USERNAME', '')}\n")
                f.write(f"TWITTER_PASSWORD={env_vars.get('TWITTER_PASSWORD', '')}\n")
    
    def create_systemd_service(self):
        """Create a systemd service file (Linux only)"""
        if not self.is_linux:
            logger.info("Systemd service creation is only supported on Linux")
            return
        
        if not self.args.service:
            logger.info("Skipping systemd service creation (use --service to enable)")
            return
        
        logger.info("Creating systemd service")
        
        service_file = f"""[Unit]
Description=MultiversX AI Twitter Bot
After=network.target

[Service]
User={os.getenv('USER')}
WorkingDirectory={self.project_root}
ExecStart={self.python_cmd} {os.path.join(self.src_dir, 'main.py')}
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        service_path = os.path.join("/tmp", f"{self.service_name}.service")
        
        with open(service_path, "w") as f:
            f.write(service_file)
        
        logger.info(f"Created service file at {service_path}")
        logger.info("Installing service (requires sudo)...")
        
        try:
            self.run_command(["sudo", "mv", service_path, f"/etc/systemd/system/{self.service_name}.service"])
            self.run_command(["sudo", "systemctl", "daemon-reload"])
            self.run_command(["sudo", "systemctl", "enable", self.service_name])
            logger.info(f"Service installed. Start with: sudo systemctl start {self.service_name}")
        except Exception as e:
            logger.error(f"Error installing service: {e}")
            logger.info(f"Manual installation: sudo mv {service_path} /etc/systemd/system/{self.service_name}.service")
    
    def create_startup_script(self):
        """Create startup scripts for different platforms"""
        logger.info("Creating startup scripts")
        
        if self.is_windows:
            # Create Windows batch file
            batch_file = os.path.join(self.project_root, "start_bot.bat")
            with open(batch_file, "w") as f:
                f.write(f"@echo off\n")
                f.write(f"cd {self.project_root}\n")
                f.write(f"{self.venv_dir}\\Scripts\\python.exe {self.src_dir}\\main.py\n")
                f.write("pause\n")
            
            logger.info(f"Created Windows startup script: {batch_file}")
        
        # Create shell script for Unix-like systems
        sh_file = os.path.join(self.project_root, "start_bot.sh")
        with open(sh_file, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"cd {self.project_root}\n")
            f.write(f"{self.venv_dir}/bin/python {self.src_dir}/main.py\n")
        
        # Make shell script executable
        if not self.is_windows:
            os.chmod(sh_file, 0o755)
        
        logger.info(f"Created shell startup script: {sh_file}")
    
    def run_tests(self):
        """Run tests if available"""
        test_dir = os.path.join(self.project_root, "tests")
        
        if not os.path.exists(test_dir):
            logger.info("No tests directory found, skipping tests")
            return
        
        logger.info("Running tests")
        
        # Check if pytest is installed
        try:
            self.run_command([self.pip_cmd, "install", "pytest"])
            
            # Run tests
            result = self.run_command([self.python_cmd, "-m", "pytest", test_dir], check=False)
            
            if result.returncode != 0:
                logger.warning("Some tests failed")
                if self.args.strict:
                    logger.error("Deployment aborted due to test failures (--strict mode)")
                    sys.exit(1)
            else:
                logger.info("All tests passed")
                
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            if self.args.strict:
                sys.exit(1)
    
    def deploy(self):
        """Run the full deployment process"""
        logger.info("Starting deployment")
        
        try:
            # Create backup first
            if self.args.backup:
                self.backup_data()
            
            # Setup environment
            self.create_virtual_environment()
            self.install_dependencies()
            self.configure_environment()
            
            # Run tests
            if self.args.test:
                self.run_tests()
            
            # Create startup scripts
            self.create_startup_script()
            
            # Create systemd service if requested
            self.create_systemd_service()
            
            logger.info("Deployment completed successfully")
            
            # Start the bot if requested
            if self.args.start:
                logger.info("Starting the bot")
                
                if self.is_linux and self.args.service:
                    self.run_command(["sudo", "systemctl", "start", self.service_name])
                else:
                    self.start()
                
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            sys.exit(1)
    
    def start(self):
        """Start the bot"""
        logger.info("Starting MultiversX AI Twitter Bot")
        
        try:
            cmd = [self.python_cmd, os.path.join(self.src_dir, "main.py")]
            
            if self.args.daemon:
                # Start in background
                if self.is_windows:
                    # Windows - use subprocess.Popen (no easy daemon mode)
                    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # Unix - use nohup
                    nohup_cmd = f"nohup {self.python_cmd} {os.path.join(self.src_dir, 'main.py')} > bot.log 2>&1 &"
                    subprocess.Popen(nohup_cmd, shell=True)
            else:
                # Start in foreground
                subprocess.run(cmd)
                
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            sys.exit(1)
    
    def stop(self):
        """Stop the bot"""
        logger.info("Stopping MultiversX AI Twitter Bot")
        
        if self.is_linux and self.args.service:
            try:
                self.run_command(["sudo", "systemctl", "stop", self.service_name])
                logger.info("Bot stopped via systemd")
                return
            except Exception as e:
                logger.error(f"Error stopping bot via systemd: {e}")
        
        # Find and kill the process
        try:
            if self.is_windows:
                # Windows - use taskkill
                self.run_command(["taskkill", "/F", "/IM", "python.exe", "/FI", f"WINDOWTITLE eq MultiversX AI Twitter Bot"], check=False)
            else:
                # Unix - use pkill or killall
                self.run_command(["pkill", "-f", "main.py"], check=False)
                
            logger.info("Bot process stopped")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="MultiversX AI Twitter Bot Deployment Tool")
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--deploy", action="store_true", help="Deploy the bot with full setup")
    action_group.add_argument("--start", action="store_true", help="Start the bot")
    action_group.add_argument("--stop", action="store_true", help="Stop the bot")
    
    # Optional arguments
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files")
    parser.add_argument("--backup", action="store_true", help="Create backup before deploying")
    parser.add_argument("--test", action="store_true", help="Run tests before deploying")
    parser.add_argument("--strict", action="store_true", help="Abort deployment if tests fail")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode for configuration")
    parser.add_argument("--with-sdk", action="store_true", help="Install MultiversX SDK")
    parser.add_argument("--service", action="store_true", help="Create systemd service (Linux only)")
    parser.add_argument("--daemon", action="store_true", help="Run in background mode")
    
    args = parser.parse_args()
    
    manager = DeploymentManager(args)
    
    if args.deploy:
        manager.deploy()
    elif args.start:
        manager.start()
    elif args.stop:
        manager.stop()

if __name__ == "__main__":
    main()