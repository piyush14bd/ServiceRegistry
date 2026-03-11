"""
Consul Service Registry Client

This demonstrates how to use HashiCorp Consul for service discovery,
comparing it with our custom implementation.

Prerequisites:
    pip install python-consul
    
    # Run Consul locally:
    consul agent -dev
"""

import consul
import time
import signal
import sys
from threading import Thread, Event


class ConsulServiceClient:
    """
    Service client that registers with Consul instead of our custom registry
    """
    
    def __init__(self, service_name, service_address, service_port, 
                 consul_host='localhost', consul_port=8500):
        self.service_name = service_name
        self.service_address = service_address
        self.service_port = service_port
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.service_id = f"{service_name}-{service_address}-{service_port}"
        self.stop_event = Event()
        
    def register(self):
        """Register service with Consul"""
        try:
            # Register service with health check
            self.consul.agent.service.register(
                name=self.service_name,
                service_id=self.service_id,
                address=self.service_address,
                port=self.service_port,
                tags=['python', 'example'],
                # Health check - Consul will check this endpoint
                check=consul.Check.http(
                    f"http://{self.service_address}:{self.service_port}/health",
                    interval="10s",
                    timeout="5s",
                    deregister="30s"  # Auto-deregister if unhealthy for 30s
                )
            )
            print(f"✓ Registered {self.service_name} with Consul")
            print(f"  Service ID: {self.service_id}")
            print(f"  Address: {self.service_address}:{self.service_port}")
            return True
        except Exception as e:
            print(f"✗ Registration failed: {e}")
            return False
    
    def deregister(self):
        """Deregister service from Consul"""
        try:
            self.consul.agent.service.deregister(self.service_id)
            print(f"✓ Deregistered {self.service_name}")
            return True
        except Exception as e:
            print(f"✗ Deregistration failed: {e}")
            return False
    
    def discover_service(self, service_name):
        """Discover instances of a service"""
        try:
            # Get healthy instances only
            index, services = self.consul.health.service(
                service_name,
                passing=True  # Only return healthy services
            )
            
            instances = []
            for service in services:
                instances.append({
                    'id': service['Service']['ID'],
                    'address': service['Service']['Address'],
                    'port': service['Service']['Port'],
                    'tags': service['Service']['Tags']
                })
            
            print(f"\n🔍 Discovered {service_name}:")
            print(f"   Found {len(instances)} healthy instance(s)")
            for inst in instances:
                print(f"   - {inst['address']}:{inst['port']} (ID: {inst['id']})")
            
            return instances
        except Exception as e:
            print(f"✗ Discovery failed: {e}")
            return []
    
    def get_all_services(self):
        """List all registered services"""
        try:
            services = self.consul.agent.services()
            
            print("\n📋 All Services in Consul:")
            for service_id, service_info in services.items():
                print(f"   - {service_info['Service']} ({service_id})")
                print(f"     Address: {service_info['Address']}:{service_info['Port']}")
            
            return services
        except Exception as e:
            print(f"✗ Failed to list services: {e}")
            return {}
    
    def watch_service(self, service_name, callback):
        """
        Watch for changes to a service (blocking call)
        This is a powerful Consul feature - get notified when services change
        """
        index = None
        while not self.stop_event.is_set():
            try:
                index, services = self.consul.health.service(
                    service_name,
                    passing=True,
                    index=index,
                    wait='30s'  # Long polling
                )
                
                if services:
                    callback(services)
                    
            except Exception as e:
                print(f"Watch error: {e}")
                time.sleep(5)
    
    def start(self):
        """Start the service"""
        if not self.register():
            print("Failed to register. Exiting.")
            return
        
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


def demo_consul():
    """Demonstrate Consul features"""
    print("\n" + "="*60)
    print("CONSUL SERVICE DISCOVERY DEMO")
    print("="*60)
    
    try:
        # Connect to Consul
        c = consul.Consul()
        
        # Check if Consul is running
        leader = c.status.leader()
        print(f"✓ Connected to Consul (Leader: {leader})\n")
        
        # List all services
        services = c.agent.services()
        print(f"📋 Currently registered services: {len(services)}")
        for service_id, service_info in services.items():
            print(f"   - {service_info['Service']} at {service_info['Address']}:{service_info['Port']}")
        
        print("\n" + "="*60)
        print("Consul Features Demonstrated:")
        print("="*60)
        print("✅ Service Registration")
        print("✅ Health Checking (automatic)")
        print("✅ Service Discovery")
        print("✅ Auto-deregistration of unhealthy services")
        print("✅ Tags and metadata")
        print("✅ Watch for service changes (long polling)")
        print("\n")
        
    except Exception as e:
        print(f"✗ Cannot connect to Consul: {e}")
        print("\nTo start Consul:")
        print("  consul agent -dev")
        print("\nOr with Docker:")
        print("  docker run -d -p 8500:8500 consul:latest")


def compare_implementations():
    """Compare our custom registry with Consul"""
    print("\n" + "="*60)
    print("COMPARISON: Custom Registry vs Consul")
    print("="*60)
    
    comparison = """
    
Feature                     | Custom Registry      | Consul
---------------------------|---------------------|----------------------
Service Registration       | ✅ Manual API       | ✅ Agent API
Health Checking            | ✅ Heartbeat        | ✅ Active checks
Auto-deregistration        | ✅ Timeout-based    | ✅ Health-based
Service Discovery          | ✅ REST API         | ✅ DNS + HTTP API
Watch for Changes          | ❌ Polling only     | ✅ Long polling/blocking
Multi-datacenter           | ❌ Single instance  | ✅ Built-in
Key-Value Store            | ❌ Not included     | ✅ Included
ACLs/Security              | ❌ Not included     | ✅ Built-in
UI Dashboard               | ❌ Not included     | ✅ Built-in
Production Ready           | ❌ Learning only    | ✅ Battle-tested
Complexity                 | ✅ Simple           | ⚠️  More complex
Learning Curve             | ✅ Easy             | ⚠️  Moderate

WHEN TO USE EACH:

Custom Registry:
  ✅ Learning service discovery concepts
  ✅ Simple microservices projects
  ✅ Understanding the fundamentals
  ✅ Prototyping and experimentation

Consul:
  ✅ Production environments
  ✅ Multi-datacenter deployments
  ✅ Need for advanced features (KV store, ACLs)
  ✅ Large-scale microservices
  ✅ Enterprise requirements
    """
    
    print(comparison)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python consul_client.py demo              # Show Consul features")
        print("  python consul_client.py compare           # Compare implementations")
        print("  python consul_client.py <service> <port>  # Register a service")
        print("\nExamples:")
        print("  python consul_client.py demo")
        print("  python consul_client.py user-service 8001")
        print("  python consul_client.py payment-service 8002")
        sys.exit(1)
    
    if sys.argv[1] == "demo":
        demo_consul()
    elif sys.argv[1] == "compare":
        compare_implementations()
    else:
        service_name = sys.argv[1]
        port = int(sys.argv[2])
        
        client = ConsulServiceClient(
            service_name=service_name,
            service_address="127.0.0.1",
            service_port=port
        )
        client.start()

# Made with Bob
