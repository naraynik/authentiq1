# 📦 AuthentiQ Deployment Guide

## Deployment Options

### 1. Local Development (Docker Compose)
```bash
docker-compose -f docker-compose.dev.yml up
```
Best for: Learning, testing, development

---

### 2. Full Docker Stack
```bash
docker-compose -f docker-compose.full.yml up --build
```
Includes: PostgreSQL + Backend + Blockchain + Frontend
Best for: Demo, integration testing

---

### 3. Cloud Deployment

## AWS Deployment

### Backend (ECS/Fargate)

#### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name authentiq-backend --region us-east-1
```

#### 2. Build & Push Docker Image
```bash
# Build
docker build -f infrastructure/Dockerfile.backend -t authentiq-backend .

# Tag
docker tag authentiq-backend:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/authentiq-backend:latest

# Push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/authentiq-backend:latest
```

#### 3. Create RDS PostgreSQL
```bash
aws rds create-db-instance \
  --db-instance-identifier authentiq-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password <STRONG_PASSWORD> \
  --allocated-storage 20 \
  --publicly-accessible false
```

#### 4. Deploy to ECS
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name authentiq

# Register task definition (use Dockerfile)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster authentiq \
  --service-name authentiq-service \
  --task-definition authentiq-task:1 \
  --desired-count 1 \
  --launch-type FARGATE
```

### Frontend (S3 + CloudFront)

#### 1. Build Frontend
```bash
cd frontend
npm run build
```

#### 2. Upload to S3
```bash
aws s3 sync out s3://authentiq-frontend --delete
```

#### 3. Create CloudFront Distribution
```bash
aws cloudfront create-distribution --distribution-config-with-tags file://cf-config.json
```

---

## Google Cloud Deployment

### Backend (Cloud Run)

```bash
# Build image
docker build -f infrastructure/Dockerfile.backend -t authentiq-backend .

# Push to Google Container Registry
docker tag authentiq-backend gcr.io/YOUR_PROJECT/authentiq-backend
docker push gcr.io/YOUR_PROJECT/authentiq-backend

# Deploy to Cloud Run
gcloud run deploy authentiq-backend \
  --image gcr.io/YOUR_PROJECT/authentiq-backend \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --env-vars-file .env.cloud
```

### Database (Cloud SQL)

```bash
gcloud sql instances create authentiq-db \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region us-central1

gcloud sql databases create authentiq --instance authentiq-db
```

### Frontend (Firebase Hosting)

```bash
cd frontend
npm run build

firebase deploy --only hosting
```

---

## Azure Deployment

### Backend (App Service)

```bash
# Create resource group
az group create --name authentiq-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name authentiq-plan \
  --resource-group authentiq-rg \
  --sku B1 --is-linux

# Deploy
az webapp deployment source config-zip \
  --resource-group authentiq-rg \
  --name authentiq-backend \
  --src ./backend.zip
```

### Database (Azure Database for PostgreSQL)

```bash
az postgres flexible-server create \
  --resource-group authentiq-rg \
  --name authentiq-db \
  --location eastus \
  --admin-user postgres \
  --admin-password <PASSWORD>
```

---

## Blockchain Deployment

### Deploy to Polygon (Recommended)

#### 1. Setup Hardhat Config
```javascript
// blockchain/hardhat.config.js
networks: {
  polygon: {
    url: `https://polygon-rpc.com`,
    accounts: [process.env.DEPLOYER_PRIVATE_KEY]
  }
}
```

#### 2. Deploy Contract
```bash
cd blockchain
DEPLOYER_PRIVATE_KEY=<YOUR_KEY> npx hardhat run scripts/deploy.js --network polygon
```

#### 3. Verify on Block Explorer
```bash
npx hardhat verify --network polygon <CONTRACT_ADDRESS>
```

### Deploy to Ethereum

```bash
# Configure Infura or Alchemy provider
ALCHEMY_KEY=<YOUR_KEY> npx hardhat run scripts/deploy.js --network ethereum
```

---

## Environment Variables (Production)

Create `.env.production`:
```env
# Database
DATABASE_URL=postgresql://user:password@authentiq-db.postgres.database.azure.com:5432/authentiq

# Blockchain
RPC_URL=https://polygon-rpc.com
CONTRACT_ADDRESS=0x...  # From deployment

# AI Models
RF_MODEL_PATH=/app/models/rf_model.joblib
GNN_MODEL_PATH=/app/models/gnn_model.pt

# API
BACKEND_URL=https://api.authentiq.app
FRONTEND_URL=https://authentiq.app

# Security
SECRET_KEY=<GENERATE_RANDOM_STRING>
CORS_ORIGINS=https://authentiq.app

# Environment
ENVIRONMENT=production
DEBUG=false
```

---

## SSL/TLS Certificate

### AWS (ACM)
```bash
aws acm request-certificate \
  --domain-name authentiq.app \
  --subject-alternative-names www.authentiq.app \
  --validation-method DNS
```

### Let's Encrypt (Free)
```bash
# Using Certbot
certbot certonly --standalone -d authentiq.app -d www.authentiq.app
```

---

## Monitoring & Logging

### AWS CloudWatch
```bash
# View logs
aws logs tail /aws/ecs/authentiq --follow
```

### Google Cloud Logging
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

### Azure Monitor
```bash
az monitor metrics list --resource-group authentiq-rg --resource authentiq-backend
```

### Application Insights
```bash
az monitor app-insights component show --app authentiq --resource-group authentiq-rg
```

---

## Auto-Scaling

### AWS Auto Scaling
```bash
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name authentiq-asg \
  --launch-configuration authentiq-lc \
  --min-size 1 \
  --max-size 10 \
  --desired-capacity 2
```

### Google Cloud Autoscaling
```bash
gcloud run deploy authentiq-backend \
  --image gcr.io/YOUR_PROJECT/backend \
  --max-instances 10
```

---

## Database Backups

### AWS RDS Automated Backups
```bash
aws rds modify-db-instance \
  --db-instance-identifier authentiq-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"
```

### Manual Backup
```bash
pg_dump -U postgres authentiq > backup.sql
```

### Restore
```bash
psql -U postgres authentiq < backup.sql
```

---

## CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy Backend
        run: |
          docker build -f infrastructure/Dockerfile.backend -t authentiq-backend .
          docker push authentiq-backend
      
      - name: Deploy Frontend
        run: |
          cd frontend
          npm install
          npm run build
          npm run export
      
      - name: Create Release
        uses: actions/create-release@v1
```

---

## Post-Deployment Checklist

- [ ] Database backups configured
- [ ] SSL certificate installed
- [ ] CDN configured (CloudFront/Cloudflare)
- [ ] WAF rules set up
- [ ] Monitoring alerts configured
- [ ] Auto-scaling policies set
- [ ] Load balancer health checks enabled
- [ ] API rate limiting enabled
- [ ] CORS policy restricted
- [ ] Environment variables secured
- [ ] Database connection encrypted
- [ ] Smart contract verified on block explorer
- [ ] Domain DNS records updated
- [ ] Analytics configured (Google Analytics, Mixpanel)

---

## Troubleshooting Deployment

| Issue | Solution |
|-------|----------|
| Container won't start | Check logs: `docker logs -f container_name` |
| Database connection fails | Verify security groups/firewalls allow traffic |
| API returns 500 | Check environment variables and secrets |
| Frontend shows 404 | Verify API endpoint URL in config |
| Contract deploy fails | Check deployer has funds, correct RPC URL |
| High latency | Enable caching, check database indexes |

---

## Cost Optimization

| Service | Budget Tips |
|---------|------------|
| Database | Use managed service, set auto-pause |
| Compute | Start with micro instances, scale as needed |
| Storage | Enable S3/disk lifecycle policies |
| CDN | Cache static assets aggressively |
| Blockchain | Use Layer 2 (Polygon) to reduce gas fees |

---

## Rollback Procedure

```bash
# Keep previous deployments
docker tag authentiq-backend:v1 authentiq-backend:v1-backup

# Rollback if needed
docker pull authentiq-backend:v0
docker run -d authentiq-backend:v0
```

---

**Want hands-on deployment help? Reach out to the team!**

