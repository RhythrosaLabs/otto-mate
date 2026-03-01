#!/usr/bin/env python3
"""
Otto Universal - Onboarding Wizard
==================================

Interactive setup wizard for new Otto users.
Checks environment, validates API keys, and guides through configuration.

Usage:
    python scripts/onboarding.py
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")


def print_step(step: int, total: int, text: str):
    """Print a step indicator."""
    print(f"\n{Colors.BLUE}[Step {step}/{total}]{Colors.ENDC} {Colors.BOLD}{text}{Colors.ENDC}")
    print("-" * 50)


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


class OnboardingWizard:
    """Interactive onboarding wizard for Otto setup."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.env_file = self.project_root / ".env"
        self.config: Dict[str, str] = {}
        self.checks_passed: List[str] = []
        self.checks_failed: List[str] = []
        self.checks_warnings: List[str] = []
    
    def load_existing_env(self) -> Dict[str, str]:
        """Load existing .env file if present."""
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
        return env_vars
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            print_success(f"Python {version.major}.{version.minor}.{version.micro} (3.10+ required)")
            self.checks_passed.append("python_version")
            return True
        else:
            print_error(f"Python {version.major}.{version.minor}.{version.micro} - Python 3.10+ required")
            self.checks_failed.append("python_version")
            return False
    
    def check_required_dirs(self) -> bool:
        """Check and create required directories."""
        required_dirs = [
            "data",
            "data/uploads",
            "data/conversations",
            "data/workflows",
            "data/projects",
            "data/agents",
            "data/brand_brain",
            "logs",
        ]
        
        all_ok = True
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print_info(f"Created directory: {dir_path}")
            else:
                pass  # Directory exists, no need to print
        
        print_success("All required directories present")
        self.checks_passed.append("directories")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if required packages are installed."""
        required_packages = [
            ("fastapi", "FastAPI web framework"),
            ("anthropic", "Anthropic Claude API"),
            ("openai", "OpenAI API"),
            ("pydantic", "Data validation"),
            ("uvicorn", "ASGI server"),
        ]
        
        missing = []
        for package, desc in required_packages:
            try:
                __import__(package)
                print_success(f"{desc} ({package})")
            except ImportError:
                print_error(f"{desc} ({package}) - NOT INSTALLED")
                missing.append(package)
        
        if missing:
            print_warning(f"Install missing packages: pip install {' '.join(missing)}")
            self.checks_warnings.append("dependencies")
            return False
        
        self.checks_passed.append("dependencies")
        return True
    
    def check_api_keys(self) -> Tuple[bool, Dict[str, bool]]:
        """Check which API keys are configured."""
        env = self.load_existing_env()
        
        # Also check environment variables
        for key in os.environ:
            if key.endswith('_API_KEY') or key.endswith('_API_TOKEN') or key.endswith('_API_SECRET'):
                if key not in env:
                    env[key] = os.environ[key]
        
        api_keys = {
            "ANTHROPIC_API_KEY": ("Anthropic Claude", True),  # Required
            "OPENAI_API_KEY": ("OpenAI (optional)", False),
            "REPLICATE_API_TOKEN": ("Replicate AI (images/video)", False),
            "PRINTIFY_API_KEY": ("Printify (print-on-demand)", False),
            "SHOPIFY_API_KEY": ("Shopify (e-commerce)", False),
            "SERPER_API_KEY": ("Serper (web search)", False),
        }
        
        results = {}
        has_required = True
        
        for key, (desc, required) in api_keys.items():
            value = env.get(key, "")
            is_set = bool(value) and value not in ("your_key_here", "")
            results[key] = is_set
            
            if is_set:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print_success(f"{desc}: {masked}")
            elif required:
                print_error(f"{desc}: NOT SET (Required)")
                has_required = False
            else:
                print_warning(f"{desc}: Not configured (optional)")
        
        if has_required:
            self.checks_passed.append("api_keys")
        else:
            self.checks_failed.append("api_keys")
        
        return has_required, results
    
    def prompt_api_key(self, key_name: str, description: str, required: bool = False) -> Optional[str]:
        """Prompt user for an API key."""
        req_label = " (required)" if required else " (optional - press Enter to skip)"
        print(f"\n{Colors.BOLD}{description}{req_label}{Colors.ENDC}")
        
        if key_name == "ANTHROPIC_API_KEY":
            print(f"{Colors.CYAN}Get your API key at: https://console.anthropic.com/{Colors.ENDC}")
        elif key_name == "OPENAI_API_KEY":
            print(f"{Colors.CYAN}Get your API key at: https://platform.openai.com/api-keys{Colors.ENDC}")
        elif key_name == "REPLICATE_API_TOKEN":
            print(f"{Colors.CYAN}Get your token at: https://replicate.com/account/api-tokens{Colors.ENDC}")
        elif key_name == "PRINTIFY_API_KEY":
            print(f"{Colors.CYAN}Get your token at: https://printify.com/app/account/api{Colors.ENDC}")
        
        while True:
            value = input(f"Enter {key_name}: ").strip()
            if value:
                return value
            elif not required:
                return None
            else:
                print_warning("This key is required. Please enter a value.")
    
    def save_env_file(self, config: Dict[str, str]):
        """Save configuration to .env file."""
        # Load existing config
        existing = self.load_existing_env()
        existing.update(config)
        
        # Build new .env content
        lines = [
            "# Otto Universal Configuration",
            f"# Generated by onboarding wizard on {datetime.now().isoformat()}",
            "",
            "# === Required API Keys ===",
        ]
        
        # Group keys by category
        categories = {
            "AI Services": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "REPLICATE_API_TOKEN"],
            "E-commerce": ["PRINTIFY_API_KEY", "PRINTIFY_SHOP_ID", "SHOPIFY_API_KEY", "SHOPIFY_API_SECRET", "SHOPIFY_SHOP_NAME"],
            "Search & Web": ["SERPER_API_KEY"],
            "Other": []
        }
        
        written_keys = set()
        for category, keys in categories.items():
            section_lines = []
            for key in keys:
                if key in existing and existing[key]:
                    section_lines.append(f"{key}={existing[key]}")
                    written_keys.add(key)
            
            if section_lines:
                lines.append(f"\n# === {category} ===")
                lines.extend(section_lines)
        
        # Add any remaining keys
        remaining = []
        for key, value in existing.items():
            if key not in written_keys and value:
                remaining.append(f"{key}={value}")
        
        if remaining:
            lines.append("\n# === Other Settings ===")
            lines.extend(remaining)
        
        # Write file
        with open(self.env_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print_success(f"Configuration saved to {self.env_file}")
    
    def test_anthropic_connection(self, api_key: str) -> bool:
        """Test connection to Anthropic API."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            # Quick test message
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'OK'"}]
            )
            print_success("Anthropic API connection verified!")
            return True
        except Exception as e:
            print_error(f"Anthropic API test failed: {e}")
            return False
    
    def run_interactive(self):
        """Run the interactive onboarding wizard."""
        print_header("Otto Universal - Setup Wizard")
        
        print("Welcome to Otto, your AI-powered business assistant!")
        print("This wizard will help you set up your environment.\n")
        
        # Step 1: System checks
        print_step(1, 5, "Checking System Requirements")
        self.check_python_version()
        self.check_required_dirs()
        
        # Step 2: Dependencies
        print_step(2, 5, "Checking Dependencies")
        deps_ok = self.check_dependencies()
        if not deps_ok:
            print("\nRun: pip install -r requirements.txt")
            response = input("\nContinue anyway? (y/n): ").strip().lower()
            if response != 'y':
                print("\nPlease install dependencies and run the wizard again.")
                sys.exit(1)
        
        # Step 3: API Keys
        print_step(3, 5, "Checking API Configuration")
        keys_ok, key_status = self.check_api_keys()
        
        if not keys_ok or not key_status.get("ANTHROPIC_API_KEY"):
            print("\n" + "=" * 50)
            response = input("\nWould you like to configure API keys now? (y/n): ").strip().lower()
            
            if response == 'y':
                new_config = {}
                
                # Required: Anthropic
                if not key_status.get("ANTHROPIC_API_KEY"):
                    key = self.prompt_api_key(
                        "ANTHROPIC_API_KEY",
                        "Anthropic Claude API Key",
                        required=True
                    )
                    if key:
                        new_config["ANTHROPIC_API_KEY"] = key
                
                # Optional keys
                for key_name, desc in [
                    ("REPLICATE_API_TOKEN", "Replicate API Token (for AI images/video)"),
                    ("PRINTIFY_API_KEY", "Printify API Key (for print-on-demand)"),
                    ("SERPER_API_KEY", "Serper API Key (for web search)"),
                ]:
                    if not key_status.get(key_name):
                        key = self.prompt_api_key(key_name, desc, required=False)
                        if key:
                            new_config[key_name] = key
                
                if new_config:
                    self.save_env_file(new_config)
        
        # Step 4: Test connection
        print_step(4, 5, "Testing Connections")
        env = self.load_existing_env()
        anthropic_key = env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        
        if anthropic_key:
            print_info("Testing Anthropic API connection...")
            self.test_anthropic_connection(anthropic_key)
        else:
            print_warning("Skipping connection test - no API key configured")
        
        # Step 5: Summary
        print_step(5, 5, "Setup Summary")
        
        print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        print(f"  Checks Passed: {len(self.checks_passed)}")
        print(f"  Checks Failed: {len(self.checks_failed)}")
        print(f"  Warnings: {len(self.checks_warnings)}")
        
        if self.checks_failed:
            print(f"\n{Colors.RED}Failed checks:{Colors.ENDC}")
            for check in self.checks_failed:
                print(f"  - {check}")
        
        # Final instructions
        print_header("Getting Started")
        
        print(f"""
{Colors.BOLD}Start Otto:{Colors.ENDC}
  python run.py
  
{Colors.BOLD}Or with uvicorn directly:{Colors.ENDC}
  uvicorn src.api.main:app --reload --port 8000

{Colors.BOLD}Access Otto:{Colors.ENDC}
  - Web UI: http://localhost:8000
  - API Docs: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health

{Colors.BOLD}Quick Commands:{Colors.ENDC}
  Try these slash commands in the chat:
  - /help - Show all available commands
  - /status - Check system status
  - /models - List AI models
  - /tools - List available tools

{Colors.BOLD}Documentation:{Colors.ENDC}
  - README.md - Getting started
  - docs/GETTING_STARTED.md - Detailed guide
  - docs/QUICK_START_GUIDE.md - Quick reference
""")
        
        if not self.checks_failed:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ Otto is ready to use!{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Please resolve the issues above before starting Otto.{Colors.ENDC}")
    
    def run_quick_check(self):
        """Run a quick status check without interaction."""
        print_header("Otto Quick Check")
        
        self.check_python_version()
        self.check_required_dirs()
        self.check_dependencies()
        self.check_api_keys()
        
        print("\n" + "=" * 50)
        if not self.checks_failed:
            print(f"{Colors.GREEN}All checks passed! Run 'python run.py' to start Otto.{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}Some checks failed. Run 'python scripts/onboarding.py' for setup wizard.{Colors.ENDC}")


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Otto Onboarding Wizard")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick check mode")
    args = parser.parse_args()
    
    wizard = OnboardingWizard()
    
    if args.quick:
        wizard.run_quick_check()
    else:
        wizard.run_interactive()


if __name__ == "__main__":
    main()
