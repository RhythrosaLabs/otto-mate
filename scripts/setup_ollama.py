#!/usr/bin/env python3
"""
Otto Ollama Setup Script
Automatically install Ollama and download recommended models
"""

import os
import sys
import platform
import subprocess
import urllib.request
import json
from pathlib import Path
import time


class OllamaSetup:
    """Automated Ollama installation and model setup"""
    
    def __init__(self):
        self.system = platform.system()
        self.machine = platform.machine()
        self.ollama_installed = False
        self.ollama_running = False
        
    def print_header(self):
        """Print welcome header"""
        print("=" * 70)
        print("🚀 OTTO OLLAMA SETUP - Local AI Model Manager")
        print("=" * 70)
        print()
        print("This script will help you:")
        print("  1. Install Ollama (if not already installed)")
        print("  2. Start the Ollama service")
        print("  3. Download recommended AI models")
        print()
        
    def check_ollama_installed(self):
        """Check if Ollama is already installed"""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Ollama is already installed:", result.stdout.strip())
                self.ollama_installed = True
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        print("❌ Ollama is not installed")
        return False
    
    def check_ollama_running(self):
        """Check if Ollama service is running"""
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                print(f"✅ Ollama is running (version {data.get('version', 'unknown')})")
                self.ollama_running = True
                return True
        except:
            pass
        
        print("❌ Ollama service is not running")
        return False
    
    def install_ollama_mac(self):
        """Install Ollama on macOS"""
        print("\n📥 Installing Ollama on macOS...")
        print("This will download and run the Ollama installer.")
        
        if input("Continue? (y/n): ").lower() != 'y':
            print("Installation cancelled.")
            return False
        
        try:
            # Download installer
            url = "https://ollama.ai/download/Ollama-darwin.zip"
            temp_file = "/tmp/Ollama-darwin.zip"
            
            print("Downloading installer...")
            urllib.request.urlretrieve(url, temp_file)
            
            # Unzip and install
            print("Installing...")
            subprocess.run(["unzip", "-o", temp_file, "-d", "/tmp/"], check=True)
            subprocess.run(["open", "/tmp/Ollama.app"], check=True)
            
            print("\n✅ Ollama installer opened!")
            print("   Please complete the installation, then run this script again.")
            return True
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            print("\nManual installation:")
            print("1. Visit: https://ollama.ai/download")
            print("2. Download Ollama for macOS")
            print("3. Install and run this script again")
            return False
    
    def install_ollama_linux(self):
        """Install Ollama on Linux"""
        print("\n📥 Installing Ollama on Linux...")
        print("This will run the official Ollama installation script.")
        
        if input("Continue? (y/n): ").lower() != 'y':
            print("Installation cancelled.")
            return False
        
        try:
            print("Running installation script...")
            result = subprocess.run(
                ["curl", "-fsSL", "https://ollama.ai/install.sh"],
                capture_output=True,
                text=True
            )
            
            # Pipe to shell
            subprocess.run(["sh"], input=result.stdout, text=True, check=True)
            
            print("\n✅ Ollama installed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            print("\nManual installation:")
            print("Run: curl -fsSL https://ollama.ai/install.sh | sh")
            return False
    
    def install_ollama_windows(self):
        """Install Ollama on Windows"""
        print("\n📥 Ollama installation on Windows:")
        print("1. Visit: https://ollama.ai/download")
        print("2. Download 'OllamaSetup.exe'")
        print("3. Run the installer")
        print("4. Once installed, run this script again")
        
        input("\nPress Enter once you've installed Ollama...")
        return self.check_ollama_installed()
    
    def install_ollama(self):
        """Install Ollama based on OS"""
        if self.system == "Darwin":  # macOS
            return self.install_ollama_mac()
        elif self.system == "Linux":
            return self.install_ollama_linux()
        elif self.system == "Windows":
            return self.install_ollama_windows()
        else:
            print(f"❌ Unsupported operating system: {self.system}")
            return False
    
    def start_ollama(self):
        """Start Ollama service"""
        print("\n🔄 Starting Ollama service...")
        
        try:
            if self.system in ["Darwin", "Linux"]:
                # Start Ollama in background
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Wait for service to start
                print("Waiting for service to start", end="")
                for _ in range(10):
                    time.sleep(1)
                    print(".", end="", flush=True)
                    if self.check_ollama_running():
                        print()
                        return True
                print()
                
            elif self.system == "Windows":
                print("Please start Ollama from the Start Menu")
                input("Press Enter once Ollama is running...")
                return self.check_ollama_running()
                
        except Exception as e:
            print(f"❌ Failed to start Ollama: {e}")
            return False
        
        return False
    
    def get_recommended_models(self):
        """Get list of recommended starter models"""
        return [
            {
                "name": "llama3.2:3b",
                "display_name": "Llama 3.2 3B",
                "description": "Fast and capable for everyday tasks",
                "size": "2.0 GB",
                "recommended": True
            },
            {
                "name": "codellama:7b",
                "display_name": "Code Llama 7B",
                "description": "Specialized for coding tasks",
                "size": "3.8 GB",
                "recommended": True
            },
            {
                "name": "nomic-embed-text",
                "display_name": "Nomic Embeddings",
                "description": "For semantic search and RAG",
                "size": "0.3 GB",
                "recommended": True
            },
            {
                "name": "mistral:7b",
                "display_name": "Mistral 7B",
                "description": "High-quality general purpose model",
                "size": "4.1 GB",
                "recommended": False
            },
            {
                "name": "llava:7b",
                "display_name": "LLaVA 7B",
                "description": "Vision model - can see images",
                "size": "4.7 GB",
                "recommended": False
            },
        ]
    
    def download_model(self, model_name):
        """Download a specific model"""
        print(f"\n📥 Downloading {model_name}...")
        print("   This may take a few minutes depending on model size...")
        
        try:
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {model_name} downloaded successfully!")
                return True
            else:
                print(f"❌ Failed to download {model_name}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def select_and_download_models(self):
        """Interactive model selection and download"""
        models = self.get_recommended_models()
        
        print("\n" + "=" * 70)
        print("📦 AVAILABLE MODELS")
        print("=" * 70)
        
        for i, model in enumerate(models, 1):
            star = "⭐" if model["recommended"] else "  "
            print(f"\n{i}. {star} {model['display_name']}")
            print(f"   Name: {model['name']}")
            print(f"   Size: {model['size']}")
            print(f"   Description: {model['description']}")
        
        print("\n" + "=" * 70)
        print("\nOptions:")
        print("  [1-5]  - Download specific model")
        print("  [all]  - Download all recommended models (⭐)")
        print("  [skip] - Skip model downloads")
        
        choice = input("\nYour choice: ").lower().strip()
        
        if choice == "skip":
            print("Skipping model downloads.")
            return True
        elif choice == "all":
            print("\n📦 Downloading starter pack...")
            total_size = sum(float(m["size"].split()[0]) for m in models if m["recommended"])
            print(f"Total download size: ~{total_size:.1f} GB")
            
            if input("Continue? (y/n): ").lower() != 'y':
                return True
            
            success = True
            for model in models:
                if model["recommended"]:
                    if not self.download_model(model["name"]):
                        success = False
            return success
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    return self.download_model(models[idx]["name"])
                else:
                    print("Invalid choice.")
                    return False
            except ValueError:
                print("Invalid input.")
                return False
    
    def verify_installation(self):
        """Verify everything is working"""
        print("\n" + "=" * 70)
        print("🔍 VERIFICATION")
        print("=" * 70)
        
        # List installed models
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("\n✅ Installed models:")
                print(result.stdout)
            else:
                print("❌ Failed to list models")
                return False
                
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
        
        print("\n" + "=" * 70)
        print("✅ Setup Complete!")
        print("=" * 70)
        print("\nYou can now:")
        print("  • Use models with Otto at http://localhost:8000")
        print("  • Browse models at http://localhost:8000/models")
        print("  • Run models directly: ollama run <model-name>")
        print("  • Chat with a model: ollama run llama3.2:3b")
        print()
        return True
    
    def run(self):
        """Run the complete setup process"""
        self.print_header()
        
        # Step 1: Check/Install Ollama
        if not self.check_ollama_installed():
            print("\n📦 Ollama needs to be installed.")
            if not self.install_ollama():
                print("\n❌ Setup failed at installation step.")
                return False
            
            # Re-check after installation
            if not self.check_ollama_installed():
                print("\n❌ Ollama installation could not be verified.")
                print("   Please run this script again after installing Ollama.")
                return False
        
        # Step 2: Start Ollama service
        if not self.check_ollama_running():
            if not self.start_ollama():
                print("\n❌ Failed to start Ollama service.")
                print("   Try starting it manually: ollama serve")
                return False
        
        # Step 3: Download models
        if not self.select_and_download_models():
            print("\n⚠️  Model download incomplete, but Ollama is ready.")
            print("   You can download models later from http://localhost:8000/models")
        
        # Step 4: Verify
        self.verify_installation()
        return True


def main():
    """Main entry point"""
    setup = OllamaSetup()
    
    try:
        success = setup.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
