#!/bin/bash
docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/blockchain-voting-repo:latest
docker run -d -p 80:5000 --name blockchain-voting-app $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/blockchain-voting-repo:latest