#!/bin/bash

# Sonic Finder - Cloud Run Deployment Script
# Este script despliega la aplicación a Google Cloud Run

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Sonic Finder - Cloud Run Deployment${NC}"
echo "========================================"
echo ""

# Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI no está instalado${NC}"
    echo "Instálalo desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Variables de configuración
read -p "Ingresa tu PROJECT_ID de Google Cloud: " PROJECT_ID
read -p "Ingresa el nombre del servicio (default: sonic-finder): " SERVICE_NAME
SERVICE_NAME=${SERVICE_NAME:-sonic-finder}
read -p "Ingresa la región (default: us-central1): " REGION
REGION=${REGION:-us-central1}

echo ""
echo -e "${YELLOW}📋 Configuración:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo ""

read -p "¿Continuar con el deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelado."
    exit 0
fi

echo ""
echo -e "${BLUE}1️⃣  Configurando proyecto...${NC}"
gcloud config set project $PROJECT_ID

echo ""
echo -e "${BLUE}2️⃣  Habilitando APIs necesarias...${NC}"
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

echo ""
echo -e "${BLUE}3️⃣  Building container image...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo ""
echo -e "${BLUE}4️⃣  Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "DATASET_PATH=data/spotify_tracks.csv,INDEX_PATH=artifacts/sklearn_model.pkl,SCALER_PATH=artifacts/scaler.pkl"

echo ""
echo -e "${GREEN}✅ ¡Deployment completado!${NC}"
echo ""

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo -e "${GREEN}🌐 Tu aplicación está disponible en:${NC}"
echo -e "${BLUE}$SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}📊 Para ver logs:${NC}"
echo "gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
echo -e "${YELLOW}💰 Para ver costos:${NC}"
echo "https://console.cloud.google.com/billing"
