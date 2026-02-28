#!/bin/bash

export APP_ENV=test
export API_DISABLE_TOKEN_AUTH=false
export SERVER_PORT=9012

python app.py
