#!/bin/bash
set -e
echo "🚀 Deploying RepoLens X..."

# Pull latest
git pull origin main

# Copy production env
cp .env.production .env

# Build and start
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Deployed! Visit https://repolens.ai"
