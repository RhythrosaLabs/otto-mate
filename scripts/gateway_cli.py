#!/usr/bin/env python3
"""
Otto Gateway CLI

Manage Gateway, channels, pairing, and more.
"""

import sys
import asyncio
import argparse
import httpx
from typing import Optional

GATEWAY_BASE = "http://localhost:8000/gateway"


async def gateway_stats():
    """Show Gateway statistics"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{GATEWAY_BASE}/stats")
        stats = response.json()
        
        print("🤖 Otto Gateway Status")
        print("=" * 50)
        print(f"Active Clients: {stats['active_clients']}")
        print(f"Uptime: {int(stats['uptime_seconds'])}s")
        print(f"Channels: {stats['channels']}")
        print(f"Total Requests: {stats['total_requests']}")


async def list_clients():
    """List connected clients"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{GATEWAY_BASE}/clients")
        clients = response.json()
        
        print(f"📱 Connected Clients ({len(clients)})")
        print("=" * 50)
        
        for c in clients:
            print(f"\n{c['device_name']} ({c['platform']})")
            print(f"  Role: {c['role']}")
            print(f"  State: {c['state']}")
            print(f"  Last Seen: {c['last_seen']}")


async def list_pending():
    """List pending pairings"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{GATEWAY_BASE}/pairing/pending")
        pending = response.json()
        
        print(f"⏳ Pending Pairings ({len(pending)})")
        print("=" * 50)
        
        for p in pending:
            device = p['device']
            print(f"\nPairing Code: {p['code']}")
            print(f"  Device: {device['device_name']} ({device['platform']})")
            print(f"  Requested: {p['requested_at']}")


async def approve_pairing(pairing_code: str):
    """Approve a pending pairing"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_BASE}/pairing/approve",
            json={"pairing_code": pairing_code}
        )
        result = response.json()
        
        if result.get("success"):
            print(f"✅ Pairing approved!")
            print(f"Device Token: {result['device_token']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")


async def test_connection():
    """Test Gateway WebSocket connection"""
    import websockets
    import json
    
    print("🔌 Testing Gateway WebSocket connection...")
    
    uri = "ws://localhost:8000/gateway/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Send connect handshake
            connect_msg = {
                "type": "connect",
                "version": "1.0.0",
                "device": {
                    "device_id": "cli_test",
                    "device_name": "CLI Test Client",
                    "platform": "cli"
                },
                "challenge": "test_challenge",
                "device_token": None
            }
            
            await websocket.send(json.dumps(connect_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            if result.get("ok"):
                if result.get("pairing_required"):
                    print(f"✅ Connection OK - Pairing required")
                    print(f"Pairing Code: {result['pairing_code']}")
                    print(f"\nRun: otto gateway approve {result['pairing_code']}")
                else:
                    print(f"✅ Connection authenticated!")
                    print(f"Device Token: {result.get('device_token', 'N/A')}")
            else:
                print(f"❌ Connection failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\nMake sure Otto is running: ./run_v2.sh")


def main():
    parser = argparse.ArgumentParser(
        description="Otto Gateway Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  otto gateway status              Show Gateway stats
  otto gateway clients             List connected clients
  otto gateway pending             List pending pairings
  otto gateway approve A3F9B2      Approve device pairing
  otto gateway test                Test WebSocket connection
        """
    )
    
    parser.add_argument("command", choices=["status", "clients", "pending", "approve", "test"], help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    
    args = parser.parse_args()
    
    try:
        if args.command == "status":
            asyncio.run(gateway_stats())
        
        elif args.command == "clients":
            asyncio.run(list_clients())
        
        elif args.command == "pending":
            asyncio.run(list_pending())
        
        elif args.command == "approve":
            if not args.args:
                print("❌ Pairing code required")
                print("Usage: otto gateway approve <pairing_code>")
                sys.exit(1)
            asyncio.run(approve_pairing(args.args[0]))
        
        elif args.command == "test":
            asyncio.run(test_connection())
    
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
        sys.exit(0)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
