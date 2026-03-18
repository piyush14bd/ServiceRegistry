"""
Example Service - Demonstrates how to register with the service registry

This simulates a microservice that:
1. Registers itself on startup
2. Sends periodic heartbeats
3. Deregisters on shutdown
"""

from __future__ import annotations

import argparse
import os
import requests
import time
import signal
import sys
from threading import Thread, Event
from flask import Flask, jsonify

class ServiceClient:
    def __init__(
        self,
        service_name: str,
        service_address: str,
        registry_url: str = "http://localhost:5001",
        heartbeat_interval: int = 10,
    ):
        self.service_name = service_name
        self.service_address = service_address
        self.registry_url = registry_url
        self.stop_event = Event()
        self.heartbeat_interval = heartbeat_interval  # seconds
        
    def register(self):
        """Register this service with the registry"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                f"{self.registry_url}/register",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                },
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Registered {self.service_name} at {self.service_address}")
                return True
            else:
                print(f"✗ Registration failed (status {response.status_code})")
                print(f"   Response: {response.text if response.text else 'Empty response'}")
                print(f"   URL: {self.registry_url}/register")
                return False
        except requests.exceptions.ConnectionError:
            print(f"✗ Cannot connect to registry at {self.registry_url}")
            print(f"   Make sure the registry is running: python3 service_registry_improved.py")
            return False
        except requests.exceptions.Timeout:
            print(f"✗ Connection timeout to registry at {self.registry_url}")
            return False
        except Exception as e:
            print(f"✗ Registration error: {e}")
            return False
    
    def deregister(self):
        """Deregister this service from the registry"""
        try:
            response = requests.post(
                f"{self.registry_url}/deregister",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                }
            )
            
            if response.status_code == 200:
                print(f"✓ Deregistered {self.service_name}")
                return True
            else:
                print(f"✗ Deregistration failed: {response.json()}")
                return False
        except Exception as e:
            print(f"✗ Deregistration error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to registry"""
        try:
            response = requests.post(
                f"{self.registry_url}/heartbeat",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                }
            )
            
            if response.status_code == 200:
                print(f"♥ Heartbeat sent for {self.service_name}")
                return True
            else:
                print(f"✗ Heartbeat failed: {response.json()}")
                return False
        except Exception as e:
            print(f"✗ Heartbeat error: {e}")
            return False
    
    def heartbeat_loop(self):
        """Background thread that sends periodic heartbeats"""
        while not self.stop_event.is_set():
            self.send_heartbeat()
            self.stop_event.wait(self.heartbeat_interval)
    
    def discover_service(self, service_name):
        """Discover instances of another service"""
        try:
            response = requests.get(f"{self.registry_url}/discover/{service_name}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n🔍 Discovered {service_name}:")
                print(f"   Found {data['count']} instance(s)")
                for instance in data['instances']:
                    print(f"   - {instance['address']} (uptime: {instance['uptime_seconds']:.1f}s)")
                return data['instances']
            else:
                print(f"✗ Discovery failed: {response.json()}")
                return []
        except Exception as e:
            print(f"✗ Discovery error: {e}")
            return []
    
    def start(self):
        """Start the service and register with registry"""
        # Register
        if not self.register():
            print("Failed to register. Exiting.")
            return
        
        # Start heartbeat thread
        heartbeat_thread = Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        print(f"\n{self.service_name} is running...")
        print("Press Ctrl+C to stop\n")
        
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n\nShutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Keep the main thread alive
        while not self.stop_event.is_set():
            time.sleep(1)
    
    def stop(self):
        """Stop the service and deregister"""
        self.stop_event.set()
        self.deregister()


def demo_service_discovery():
    """Demonstrate service discovery"""
    print("\n" + "="*60)
    print("SERVICE DISCOVERY DEMO")
    print("="*60)
    
    registry_url = "http://localhost:5001"
    
    # Check registry health
    try:
        response = requests.get(f"{registry_url}/health")
        if response.status_code == 200:
            print("✓ Registry is healthy\n")
        else:
            print("✗ Registry health check failed")
            return
    except Exception as e:
        print(f"✗ Cannot connect to registry: {e}")
        print("Make sure the registry is running on port 5001")
        return
    
    # List all services
    try:
        response = requests.get(f"{registry_url}/services")
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Total services registered: {data['total_services']}")
            for service, info in data['services'].items():
                print(f"   - {service}: {info['active_instances']} active instance(s)")
            print()
    except Exception as e:
        print(f"✗ Error listing services: {e}")


def run_http_service(
    *,
    service_name: str,
    host: str,
    port: int,
    registry_url: str,
    public_host: str | None,
    instance_id: str | None,
):
    """
    Run a real HTTP microservice instance and register it with the registry.

    - `host`/`port`: where the server binds
    - `public_host`: what gets registered (defaults to host, or POD_IP if present)
    """
    resolved_instance_id = instance_id or os.getenv("INSTANCE_ID") or f"{service_name}-{port}"

    advertised_host = (
        public_host
        or os.getenv("POD_IP")
        or (host if host not in ("0.0.0.0", "::") else "127.0.0.1")
    )
    service_address = f"http://{advertised_host}:{port}"

    client = ServiceClient(service_name=service_name, service_address=service_address, registry_url=registry_url)

    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy", "service": service_name, "instance_id": resolved_instance_id})

    @app.get("/hello")
    def hello():
        return jsonify(
            {
                "message": f"hello from {service_name}",
                "service": service_name,
                "instance_id": resolved_instance_id,
                "address": service_address,
                "timestamp": time.time(),
            }
        )

    if not client.register():
        raise SystemExit(1)

    heartbeat_thread = Thread(target=client.heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    def handle_shutdown(sig, frame):
        print("\n\nShutting down gracefully...")
        client.stop()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    print(f"✓ {service_name} serving on http://{host}:{port}")
    print(f"✓ Registered as {service_address}")
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Example microservice that registers with the service registry.")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run HTTP service + self-register + heartbeat")
    serve.add_argument("service_name")
    serve.add_argument("port", type=int)
    serve.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    serve.add_argument("--registry", default="http://localhost:5001", help="Registry base URL")
    serve.add_argument(
        "--public-host",
        default=None,
        help="Host/IP to advertise to registry (default: POD_IP env, else 127.0.0.1 when binding 0.0.0.0)",
    )
    serve.add_argument("--instance-id", default=None, help="Instance identifier (shows in /hello)")

    legacy = sub.add_parser("register-only", help="Legacy mode: register + heartbeat (no HTTP server)")
    legacy.add_argument("service_name")
    legacy.add_argument("port", type=int)
    legacy.add_argument("--registry", default="http://localhost:5001", help="Registry base URL")

    demo = sub.add_parser("demo", help="Show registry health + list services")

    args = parser.parse_args()

    if args.command == "demo":
        demo_service_discovery()
    elif args.command == "register-only":
        service_address = f"http://localhost:{args.port}"
        client = ServiceClient(args.service_name, service_address, registry_url=args.registry)
        client.start()
    elif args.command == "serve":
        run_http_service(
            service_name=args.service_name,
            host=args.host,
            port=args.port,
            registry_url=args.registry,
            public_host=args.public_host,
            instance_id=args.instance_id,
        )

# Made with Bob
