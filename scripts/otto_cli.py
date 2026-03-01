#!/usr/bin/env python3
"""
Otto Universal - Command Line Interface
=======================================

Interactive CLI for chatting with Otto from the terminal.

Usage:
    python scripts/otto_cli.py                  # Interactive mode
    python scripts/otto_cli.py "Your message"  # Single message
    python scripts/otto_cli.py /help           # Slash command
    
Options:
    --url URL       Otto API URL (default: http://localhost:8000)
    --session ID    Session ID for conversation continuity
    --json          Output raw JSON response
"""

import argparse
import json
import readline  # Enable arrow keys and history in input
import sys
from typing import Optional

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)


class Colors:
    """ANSI color codes."""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def print_banner():
    """Print Otto CLI banner."""
    print(f"""
{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════╗
║                 OTTO UNIVERSAL CLI                     ║
║            Your AI-Powered Assistant                   ║
╚═══════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.DIM}Type your message or use slash commands:
  /help    - Show available commands
  /status  - System status
  /tools   - List available tools
  /exit    - Exit CLI{Colors.RESET}
""")


def send_message(
    url: str,
    message: str,
    session_id: Optional[str] = None
) -> dict:
    """Send a message to Otto API."""
    payload = {
        "message": message,
        "session_id": session_id
    }
    
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()


def check_health(url: str) -> bool:
    """Check if Otto server is running."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{url}/health")
            return response.status_code == 200
    except:
        return False


def format_response(result: dict, raw_json: bool = False) -> str:
    """Format the API response for display."""
    if raw_json:
        return json.dumps(result, indent=2)
    
    response = result.get("response", "No response")
    msg_type = result.get("type", "unknown")
    
    # Color based on type
    if msg_type in ("error",):
        return f"{Colors.RED}{response}{Colors.RESET}"
    elif msg_type in ("help", "status", "models", "tools"):
        return f"{Colors.CYAN}{response}{Colors.RESET}"
    else:
        return f"{Colors.GREEN}{response}{Colors.RESET}"


def interactive_mode(url: str, session_id: Optional[str], raw_json: bool):
    """Run interactive chat mode."""
    print_banner()
    
    # Check server
    if not check_health(url):
        print(f"{Colors.RED}Error: Cannot connect to Otto at {url}")
        print(f"Make sure the server is running: python run.py{Colors.RESET}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}Connected to Otto at {url}{Colors.RESET}\n")
    
    # Use provided session or create one
    current_session = session_id or f"cli_{hash(str(id([]))) % 10000}"
    
    while True:
        try:
            # Get input
            user_input = input(f"{Colors.BOLD}You: {Colors.RESET}").strip()
            
            if not user_input:
                continue
            
            # Handle exit commands
            if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                print(f"\n{Colors.CYAN}Goodbye!{Colors.RESET}")
                break
            
            # Send to Otto
            print(f"{Colors.DIM}Thinking...{Colors.RESET}", end="\r")
            
            result = send_message(url, user_input, current_session)
            
            # Update session if returned
            if result.get("session_id"):
                current_session = result["session_id"]
            
            # Print response
            print(f"{Colors.BOLD}Otto: {Colors.RESET}")
            print(format_response(result, raw_json))
            print()
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Goodbye!{Colors.RESET}")
            break
        except httpx.HTTPStatusError as e:
            print(f"{Colors.RED}Error: {e.response.text}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")


def single_message_mode(
    url: str,
    message: str,
    session_id: Optional[str],
    raw_json: bool
):
    """Send a single message and exit."""
    try:
        result = send_message(url, message, session_id)
        print(format_response(result, raw_json))
    except httpx.HTTPStatusError as e:
        print(f"Error: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Otto Universal CLI - Chat with Otto from the terminal"
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send (omit for interactive mode)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Otto API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--session",
        help="Session ID for conversation continuity"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON response"
    )
    
    args = parser.parse_args()
    
    if args.message:
        single_message_mode(args.url, args.message, args.session, args.json)
    else:
        interactive_mode(args.url, args.session, args.json)


if __name__ == "__main__":
    main()
