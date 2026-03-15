# Deployment Guide

## Overview

This guide covers deploying the Swiggy RAG System in various environments.

## Prerequisites

- Python 3.12+
- Docker (optional)
- Ollama or OpenAI API key
- 2GB+ RAM
- 5GB+ disk space

## Local Deployment

### Standard Installation

```bash
# Clone repository
git clone https://github.com/uumair327/swiggy-rag-system.git
cd swiggy-rag-system

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Install Ollama (for local LLM)
brew install ollama  # macOS
# or download from https://ollama.com

# Start Ollama
ollama serve

# Pull model
ollama pull llama3.2

# Run system
python main.py ingest document.pdf
python main.py query "Your question"
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Start services
docker-compose up -d

# Pull Ollama model
docker exec swiggy-rag-ollama ollama pull llama3.2

# Ingest document
docker-compose run rag-system ingest /app/data/document.pdf

# Query
docker-compose run rag-system query "Your question"

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Docker Only

```bash
# Build image
docker build -t swiggy-rag-system .

# Run Ollama
docker run -d --name ollama -p 11434:11434 ollama/ollama
docker exec ollama ollama pull llama3.2

# Run RAG system
docker run --rm \
  --link ollama:ollama \
  -e LLM_PROVIDER=ollama \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -v $(pwd)/data:/app/data \
  swiggy-rag-system ingest /app/data/document.pdf
```

## Cloud Deployment

### AWS EC2

```bash
# Launch EC2 instance (t3.medium or larger)
# Ubuntu 22.04 LTS, 20GB storage

# SSH into instance
ssh -i key.pem ubuntu@<instance-ip>

# Install dependencies
sudo apt update
sudo apt install -y python3.12 python3.12-venv git

# Clone and setup
git clone https://github.com/uumair327/swiggy-rag-system.git
cd swiggy-rag-system
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Ollama
curl https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.2

# Configure
cp .env.example .env
# Edit .env

# Run as service (see systemd section)
```

### AWS ECS (Docker)

```yaml
# task-definition.json
{
  "family": "swiggy-rag-system",
  "containerDefinitions": [
    {
      "name": "ollama",
      "image": "ollama/ollama:latest",
      "memory": 2048,
      "portMappings": [
        {
          "containerPort": 11434,
          "protocol": "tcp"
        }
      ]
    },
    {
      "name": "rag-system",
      "image": "uumair327/swiggy-rag-system:latest",
      "memory": 2048,
      "environment": [
        {
          "name": "LLM_PROVIDER",
          "value": "ollama"
        },
        {
          "name": "OLLAMA_BASE_URL",
          "value": "http://localhost:11434"
        }
      ],
      "links": ["ollama"]
    }
  ]
}
```

### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/swiggy-rag-system

# Deploy
gcloud run deploy swiggy-rag-system \
  --image gcr.io/PROJECT_ID/swiggy-rag-system \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --set-env-vars LLM_PROVIDER=openai,OPENAI_API_KEY=sk-...
```

### Azure Container Instances

```bash
# Create resource group
az group create --name swiggy-rag-rg --location eastus

# Deploy container
az container create \
  --resource-group swiggy-rag-rg \
  --name swiggy-rag-system \
  --image uumair327/swiggy-rag-system:latest \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    LLM_PROVIDER=openai \
    OPENAI_API_KEY=sk-...
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swiggy-rag-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: swiggy-rag-system
  template:
    metadata:
      labels:
        app: swiggy-rag-system
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      - name: rag-system
        image: uumair327/swiggy-rag-system:latest
        env:
        - name: LLM_PROVIDER
          value: "ollama"
        - name: OLLAMA_BASE_URL
          value: "http://localhost:11434"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: rag-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: swiggy-rag-service
spec:
  selector:
    app: swiggy-rag-system
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/swiggy-rag-system

# Scale
kubectl scale deployment swiggy-rag-system --replicas=5
```

## Systemd Service (Linux)

```ini
# /etc/systemd/system/swiggy-rag.service
[Unit]
Description=Swiggy RAG System
After=network.target

[Service]
Type=simple
User=raguser
WorkingDirectory=/opt/swiggy-rag-system
Environment="PATH=/opt/swiggy-rag-system/venv/bin"
ExecStart=/opt/swiggy-rag-system/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable swiggy-rag
sudo systemctl start swiggy-rag
sudo systemctl status swiggy-rag

# View logs
sudo journalctl -u swiggy-rag -f
```

## Environment Configuration

### Production .env

```bash
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_TEMPERATURE=0.0

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Retrieval Settings
TOP_K_CHUNKS=5
SIMILARITY_THRESHOLD=0.3

# Chunking Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Storage
VECTOR_INDEX_PATH=/data/vector_index.faiss
CHUNKS_METADATA_PATH=/data/chunks_metadata.json

# Logging
LOG_LEVEL=INFO
```

## Performance Tuning

### Memory Optimization

```bash
# Reduce chunk size for lower memory
CHUNK_SIZE=500
CHUNK_OVERLAP=100

# Reduce top-K for faster queries
TOP_K_CHUNKS=3
```

### CPU Optimization

```bash
# Use smaller embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 384 dim, faster

# Use smaller LLM
LLM_MODEL=llama3.2  # 3B params, faster
```

## Monitoring

### Health Checks

```bash
# Docker health check
docker inspect --format='{{.State.Health.Status}}' swiggy-rag-system

# Kubernetes health check
kubectl get pods -l app=swiggy-rag-system
```

### Logging

```bash
# View logs
docker-compose logs -f rag-system
kubectl logs -f deployment/swiggy-rag-system

# Log rotation
# Configure in docker-compose.yml or k8s manifest
```

## Backup and Recovery

### Backup Vector Index

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Upload to S3
aws s3 cp backup-*.tar.gz s3://my-bucket/backups/
```

### Restore

```bash
# Download backup
aws s3 cp s3://my-bucket/backups/backup-20240314.tar.gz .

# Extract
tar -xzf backup-20240314.tar.gz

# Restart service
docker-compose restart rag-system
```

## Security Hardening

### 1. Use Non-Root User

```dockerfile
# Already configured in Dockerfile
USER raguser
```

### 2. Network Isolation

```yaml
# docker-compose.yml
networks:
  internal:
    internal: true
```

### 3. Secrets Management

```bash
# Use Docker secrets
echo "sk-..." | docker secret create openai_key -

# Reference in compose
secrets:
  - openai_key
```

### 4. TLS/SSL

```bash
# Use reverse proxy (nginx, traefik)
# Terminate SSL at proxy level
```

## Troubleshooting

### Common Issues

**"Could not connect to Ollama"**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
docker restart ollama
```

**"Out of memory"**
```bash
# Increase Docker memory limit
docker update --memory 4g swiggy-rag-system

# Or use smaller model
LLM_MODEL=llama3.2
```

**"Slow queries"**
```bash
# Reduce top-K
TOP_K_CHUNKS=3

# Use faster model
LLM_MODEL=llama3.2
```

## Cost Optimization

### Using Ollama (Free)
- No API costs
- One-time hardware investment
- Suitable for moderate usage

### Using OpenAI (Paid)
- Pay per token
- No hardware needed
- Better for high-quality responses

### Hybrid Approach
- Ollama for development/testing
- OpenAI for production
- Switch via environment variable

## Support

For deployment issues:
- GitHub Issues: https://github.com/uumair327/swiggy-rag-system/issues
- Email: support@example.com
