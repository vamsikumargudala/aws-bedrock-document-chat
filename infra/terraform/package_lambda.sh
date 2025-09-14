#!/bin/bash

# Package Lambda function for deployment
cd "$(dirname "$0")"

echo "Packaging Lambda function..."

# Create zip file with Lambda code
cp lambda_sync.py index.py
zip lambda_sync.zip index.py
rm index.py

echo "Lambda function packaged as lambda_sync.zip"