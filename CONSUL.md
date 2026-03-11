# HashiCorp Consul Integration Guide

Learn how to use production-grade service discovery with HashiCorp Consul.

## 🆚 Quick Comparison

| Feature | Our Custom Registry | Consul |
|---------|-------------------|---------|
| **Purpose** | Learning | Production |
| **Lines of Code** | ~300 | Enterprise-grade |
| **Health Checks** | Heartbeat | Active HTTP/TCP checks |
| **UI** | None | Built-in Web UI |
| **Scalability** | Single instance | Multi-datacenter |
| **Best For** | Understanding concepts | Real applications |

## 🚀 Quick Start

### 1. Install Consul

**macOS:**
```bash
brew install consul
```

**Docker:**
```bash
docker run -d -p 8500:8500 --name=consul consul agent -dev -ui -client=0.0.0.0
```

### 2. Start Consul

```bash
consul agent -dev
```

Access UI: http://localhost:8500/ui

### 3. Install Python Client

```bash
pip install python-consul
```

### 4. Use Our Consul Client

```bash
# Demo Consul features
python consul_client.py demo

# Compare with our custom registry
python consul_client.py compare

# Register a service
python consul_client.py user-service 8001
```

## 📝 Basic Usage

### Register a Service

```python
import consul

c = consul.Consul()

c.agent.service.register(
    name='user-service',
    service_id='user-1',
    address='127.0.0.1',
    port=8001,
    check=consul.Check.http('http://127.0.0.1:8001/health', interval='10s')
)
```

### Discover Services

```python
# Get healthy instances
index, services = c.health.service('user-service', passing=True)

for service in services:
    print(f"{service['Service']['Address']}:{service['Service']['Port']}")
```

### Deregister

```python
c.agent.service.deregister('user-1')
```

## 🎯 Key Features

### 1. Active Health Checks

Consul checks your services automatically:

```python
# HTTP check
check=consul.Check.http('http://127.0.0.1:8001/health', interval='10s')

# TCP check
check=consul.Check.tcp('127.0.0.1:8001', interval='10s')
```

### 2. DNS Interface

```bash
dig @127.0.0.1 -p 8600 user-service.service.consul
```

### 3. Key-Value Store

```python
# Store config
c.kv.put('config/db/host', 'localhost')

# Retrieve config
index, data = c.kv.get('config/db/host')
print(data['Value'].decode('utf-8'))
```

### 4. Watch for Changes

```python
# Get notified when services change
index = None
while True:
    index, services = c.health.service('user-service', index=index, wait='30s')
    print(f"Services changed: {len(services)} instances")
```

## 🐳 Docker Compose Example

```yaml
version: '3.8'
services:
  consul:
    image: consul:latest
    ports:
      - "8500:8500"
    command: agent -dev -ui -client=0.0.0.0
```

## 🧪 Testing

```bash
# List services
consul catalog services

# Check health
consul watch -type=service -service=user-service

# HTTP API
curl http://localhost:8500/v1/health/service/user-service?passing
```

## 📊 When to Use Each

### Use Our Custom Registry When:
- ✅ Learning service discovery concepts
- ✅ Building simple prototypes
- ✅ Understanding the fundamentals
- ✅ Educational projects

### Use Consul When:
- ✅ Production environments
- ✅ Need high availability
- ✅ Multi-datacenter deployments
- ✅ Enterprise features (ACLs, encryption)
- ✅ Service mesh capabilities

## 🎓 Learning Resources

- **Consul Docs**: https://www.consul.io/docs
- **Consul Tutorial**: https://learn.hashicorp.com/consul
- **Python Client**: https://python-consul.readthedocs.io/

## 🔄 Migration Path

1. **Start with our custom registry** - Understand the concepts
2. **Experiment with Consul locally** - See production features
3. **Deploy Consul in staging** - Test in real environment
4. **Move to production** - Use Consul for real applications

## 📝 Next Steps

1. Run `python consul_client.py demo` to see Consul in action
2. Compare features with `python consul_client.py compare`
3. Read KUBERNETES.md for container orchestration
4. Explore Consul's service mesh features

The custom registry teaches you **how it works**.  
Consul shows you **how it's done in production**. 🚀