#!/bin/bash

echo "Stopping blockchain voting container if running..."
docker stop blockchain-voting-container || true
