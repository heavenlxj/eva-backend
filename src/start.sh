#!/bin/bash

export APP_ENV=test
export API_DISABLE_TOKEN_AUTH=false
export RAG_GRPC_HOST=172.16.1.112
export RAG_GRPC_PORT=80
export WHALE_URL=http://127.0.0.1:8098

python app.py
