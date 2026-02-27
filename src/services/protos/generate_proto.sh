#!/bin/bash

# Generate Python gRPC client code from proto file
# Usage: ./generate_proto.sh

echo "Generating Python gRPC client code..."

# Check if grpc_tools is installed
if ! python -c "import grpc_tools" 2>/dev/null; then
    echo "Installing grpc_tools..."
    pip install grpcio-tools
fi

# Generate Python code from proto file
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. rag.proto

echo "Generated files:"
echo "- rag_pb2.py (message classes)"
echo "- rag_pb2_grpc.py (service classes)"

echo "Done!" 