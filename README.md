# K4 Filler Service

A cloud-native application that automates the process of filling Swedish K4 tax forms using activity statements. The application uses Anthropic's Claude AI to process PDF statements and automatically fills the appropriate fields in the K4 form.

## Features

- Automated processing of broker activity statements (PDF)
- Intelligent extraction of trade data using Claude AI
- Automatic filling of Swedish K4 tax forms
- Cloud-native architecture with Kubernetes deployment
- Real-time processing status updates
- Secure handling of sensitive information
- Downloadable filled K4 forms

## Tech Stack

### Frontend
- React.js
- Material-UI (MUI)
- Nginx (production)
- Docker

### Backend
- FastAPI (Python)
- Anthropic Claude AI
- PyPDF2 for PDF processing
- Docker
- Uvicorn server

### Infrastructure
- Google Kubernetes Engine (GKE)
- Google Container Registry (GCR)
- Kubernetes for orchestration
- Docker Compose (development)

## Local Development

### Prerequisites
- Docker and Docker Compose
- Node.js 16+
- Python 3.9+
- Anthropic API key

### Environment Setup
1. Clone the repository:
```bash
git clone [repository-url]
cd k4-filler-service
```

2. Create a `.env` file in the root directory:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

3. Run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Production Deployment to Google Cloud

### Prerequisites
- Google Cloud account with billing enabled
- gcloud CLI installed and configured
- kubectl installed
- Docker installed

### Deployment Steps

1. Set up Google Cloud Project
```bash
# Create new project
gcloud projects create k4-filler-service-2024
gcloud config set project k4-filler-service-2024

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

2. Create GKE Cluster (optimized for Sweden/Nordics)
```bash
gcloud container clusters create k4filler-cluster \
    --num-nodes=2 \
    --zone=europe-north1-a \
    --machine-type=e2-medium
```

3. Configure Docker and Build Images
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build Images
docker build -t gcr.io/k4-filler-service-2024/k4filler-frontend:latest -f frontend/Dockerfile.prod frontend/
docker build -t gcr.io/k4-filler-service-2024/k4filler-backend:latest -f backend/Dockerfile.prod backend/

# Push Images
docker push gcr.io/k4-filler-service-2024/k4filler-frontend:latest
docker push gcr.io/k4-filler-service-2024/k4filler-backend:latest
```

4. Create Kubernetes Secret for API Key
```bash
kubectl create secret generic k4filler-secrets \
    --from-literal=anthropic-api-key=your_api_key_here
```

5. Deploy to Kubernetes
```bash
kubectl apply -f k8s/
```

6. Get Application URL
```bash
kubectl get service k4filler-frontend-service
```

## Project Structure
```
k4-filler-service/
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   │   └── index.html
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── nginx.conf
├── backend/
│   ├── k4filler_service/
│   │   ├── app.py
│   │   ├── k4_document_processor.py
│   │   └── templates/
│   │       └── k4_template.pdf
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── requirements.txt
├── k8s/
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── backend-deployment.yaml
│   └── backend-service.yaml
└── docker-compose.yml
```

## Usage

1. Access the application through your browser
2. Upload your broker's activity statement (PDF)
3. Fill in the required information:
   - Tax Year
   - Broker Name
   - Account Number
   - Taxpayer Name
   - Taxpayer SIN (Personnummer)
4. Click "Process Statement"
5. Download your filled K4 form

## Maintenance and Operations

### Common Kubernetes Commands
```bash
# View all resources
kubectl get all

# Check pod status
kubectl get pods
kubectl describe pod [pod-name]

# View logs
kubectl logs -l app=k4filler-backend
kubectl logs -l app=k4filler-frontend

# Scale deployments
kubectl scale deployment k4filler-frontend --replicas=3
kubectl scale deployment k4filler-backend --replicas=3

# Update deployments (after pushing new images)
kubectl rollout restart deployment k4filler-frontend
kubectl rollout restart deployment k4filler-backend

# Delete entire deployment
kubectl delete -f k8s/
```

### Troubleshooting

1. If pods are not starting:
```bash
kubectl describe pod [pod-name]
```

2. For application logs:
```bash
kubectl logs [pod-name]
```

3. For service connectivity issues:
```bash
kubectl get service k4filler-frontend-service
```

## Security Notes

- The application uses secure secrets management in Kubernetes
- API keys are never exposed in the code or Docker images
- All communication between services is internal to the Kubernetes cluster
- Frontend-Backend communication is handled through Nginx reverse proxy

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

Tokunbo Ojo (tooj20@student.bth.se)

## Acknowledgments

- Anthropic for providing the Claude AI API
- The FastAPI and React.js communities
- Google Cloud Platform and Kubernetes teams
```

This updated README includes:
1. More detailed deployment instructions
2. Security considerations
3. Troubleshooting section
4. Detailed project structure
5. Clear usage instructions
6. Comprehensive maintenance commands
7. Specific configuration for Nordic region deployment

