#!/bin/bash

echo "Starting blockchain voting container..."

REPO_URI="084828587056.dkr.ecr.us-east-1.amazonaws.com/blockchain-voting-repo"
IMAGE_TAG=$(cat /home/ec2-user/blockchain-voting-app/imagedefinitions.json | jq -r '.[0].imageUri' | awk -F: '{print $2}')

# Pull the latest image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 084828587056.dkr.ecr.us-east-1.amazonaws.com
docker pull $REPO_URI:latest

# Start container
docker run -d --rm --name blockchain-voting-container -p 80:5000 $REPO_URI:latest

echo "Container started"
