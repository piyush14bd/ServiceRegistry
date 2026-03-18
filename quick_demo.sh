#!/bin/bash

# Quick Demo Script for Service Registry
# This script demonstrates the service registry in action

echo "=========================================="
echo "Service Registry Quick Demo"
echo "=========================================="
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed. Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "📋 This demo will:"
echo "   1. Start the service registry"
echo "   2. Start TWO instances of one microservice"
echo "   3. Both instances self-register + heartbeat"
echo "   4. Client discovers service"
echo "   5. Client calls RANDOM instance (/hello)"
echo ""
echo "Press Ctrl+C to stop at any time"
echo ""
read -p "Press Enter to continue..."

# Start registry in background
echo ""
echo "🚀 Starting Service Registry..."
python3 service_registry_improved.py > /tmp/registry.log 2>&1 &
REGISTRY_PID=$!
echo "   Registry PID: $REGISTRY_PID"

# Wait for registry to start
sleep 2

# Check if registry is running
if ! curl -s http://localhost:5001/health > /dev/null; then
    echo "❌ Failed to start registry. Check /tmp/registry.log"
    kill $REGISTRY_PID 2>/dev/null
    exit 1
fi

echo "✅ Registry is running on http://localhost:5001"
echo ""

echo "🚀 Starting TWO service instances (user-service)..."
python3 example_service.py serve user-service 8001 --host 127.0.0.1 --instance-id user-1 > /tmp/user-1.log 2>&1 &
SVC1_PID=$!
python3 example_service.py serve user-service 8002 --host 127.0.0.1 --instance-id user-2 > /tmp/user-2.log 2>&1 &
SVC2_PID=$!

sleep 2
echo "   Instance 1 PID: $SVC1_PID (log: /tmp/user-1.log)"
echo "   Instance 2 PID: $SVC2_PID (log: /tmp/user-2.log)"
echo ""

# List all services
echo "📋 Listing all registered services..."
curl -s http://localhost:5001/services | python3 -m json.tool
echo ""

# Discover user-service
echo "🔍 Discovering user-service instances..."
curl -s http://localhost:5001/discover/user-service | python3 -m json.tool
echo ""

echo "🎲 Client calling random instances..."
python3 discovery_client.py user-service --calls 12 --interval 0.75
echo ""

echo "✅ You should see instance_id switching between user-1 and user-2."
echo ""

# Cleanup
echo "🧹 Cleaning up..."
kill $SVC1_PID 2>/dev/null
kill $SVC2_PID 2>/dev/null
kill $REGISTRY_PID 2>/dev/null
echo "✅ Demo complete!"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Read README.md for detailed documentation"
echo "2. Read LEARNING_GUIDE.md for in-depth explanations"
echo "3. Try running: python3 service_registry_improved.py"
echo "4. In another terminal: python3 example_service.py user-service 8001"
echo "5. Experiment with the API endpoints!"
echo ""

# Made with Bob
