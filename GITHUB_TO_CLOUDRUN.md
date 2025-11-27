# 📦 Guía Completa: GitHub → Google Cloud Run

## ✅ Resumen de Limpieza Realizada

### Archivos Eliminados:
- ✅ `venv/` - Virtual environment
- ✅ `__pycache__/` - Cache de Python
- ✅ `eda_*.png` - Gráficos EDA (ya están en static/images/)
- ✅ `eda_analysis.py` - Script de análisis
- ✅ `example_usage.py` - Ejemplos
- ✅ Documentación redundante

### Archivos Mantenidos:
- ✅ **Código fuente completo** (main.py, api/, recommenders/)
- ✅ **Frontend** (static/, templates/)
- ✅ **Dataset** (19MB) y **modelos** (8.7MB)
- ✅ **Deployment configs** (Dockerfile, scripts)
- ✅ **Documentación esencial**

**Tamaño total**: ~30MB

---

## 🚀 Paso 1: Subir a GitHub

### 1.1 Preparar repositorio local

```bash
./prepare-github.sh
```

Este script:
- Inicializa Git (si no existe)
- Agrega todos los archivos
- Crea el commit inicial con mensaje descriptivo

### 1.2 Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre sugerido: `sonic-finder`
3. Descripción: `AI-powered music recommender using K-NN and Cosine Similarity`
4. **Público** o **Privado** (tu elección)
5. **NO** inicialices con README (ya tienes uno)
6. Click "Create repository"

### 1.3 Conectar y push

```bash
# Reemplaza TU_USUARIO con tu username de GitHub
git remote add origin https://github.com/TU_USUARIO/sonic-finder.git

# Push
git push -u origin main
```

### 1.4 Verificar

Ve a tu repo en GitHub y verifica que aparezcan:
- Código fuente ✅
- Dataset en `data/` ✅
- Modelos en `artifacts/` ✅

---

## ☁️ Paso 2: Deploy a Cloud Run desde GitHub

### Opción A: Deploy directo desde tu máquina (Más fácil)

```bash
./deploy-cloudrun.sh
```

### Opción B: Deploy desde GitHub con Cloud Build

1. **Habilitar Cloud Build GitHub App**:
   ```
   https://console.cloud.google.com/cloud-build/triggers/connect
   ```

2. **Conectar tu repositorio**

3. **Crear Trigger** con esta configuración:
   ```yaml
   Name: sonic-finder-deploy
   Event: Push to main branch
   Build configuration: Dockerfile
   Dockerfile: Dockerfile
   ```

4. **Variables de entorno** (en Cloud Run):
   ```
   DATASET_PATH=data/spotify_tracks.csv
   INDEX_PATH=artifacts/sklearn_model.pkl
   SCALER_PATH=artifacts/scaler.pkl
   ```

---

## 🔄 Workflow Completo

### Para hacer cambios:

```bash
# 1. Hacer cambios en el código
# ...

# 2. Commit
git add .
git commit -m "feat: descripción del cambio"
git push

# 3. Redeploy a Cloud Run
./deploy-cloudrun.sh
```

---

## 📊 Estructura Final del Proyecto

```
sonic-finder/
├── api/                      # API routes y models
│   ├── __init__.py
│   ├── models.py
│   └── routes.py
├── artifacts/                # Modelos entrenados
│   ├── scaler.pkl           (690B)
│   └── sklearn_model.pkl    (8.7MB)
├── data/                     # Dataset
│   └── spotify_tracks.csv   (19MB)
├── recommenders/             # Algoritmos de recomendación
│   ├── __init__.py
│   └── sklearn_recommender.py
├── static/                   # Frontend assets
│   ├── css/
│   ├── images/
│   └── js/
├── templates/                # HTML templates
│   └── index.html
├── .dockerignore            # Docker ignore
├── .env.example             # Ejemplo de variables
├── .gitignore               # Git ignore
├── CLOUD_RUN_CHECKLIST.md   # Checklist de deployment
├── DATASET_INFO.md          # Info del dataset
├── deploy-cloudrun.sh       # Script de deployment
├── DEPLOYMENT.md            # Guía de deployment
├── Dockerfile               # Container config
├── download_dataset.py      # Descarga dataset
├── main.py                  # FastAPI app
├── prepare-github.sh        # Prepara GitHub
├── README.md                # Documentación principal
├── requirements.txt         # Dependencias Python
└── run_local.sh             # Servidor local
```

---

## 🎯 Comandos Rápidos

### Local Development
```bash
./run_local.sh
```

### Git
```bash
git status                    # Ver cambios
git add .                     # Agregar archivos
git commit -m "mensaje"       # Commit
git push                      # Push a GitHub
```

### Cloud Run
```bash
./deploy-cloudrun.sh          # Deploy
gcloud run services logs tail sonic-finder --region us-central1  # Logs
```

---

## 📱 Para LinkedIn

Una vez deployado:

```markdown
🎵 Sonic Finder - Sistema de Recomendación Musical con IA

Desarrollé un recommender system que encuentra canciones similares
analizando características de audio de 114K tracks de Spotify.

🔗 Demo: https://sonic-finder-xxxxx-uc.a.run.app
💻 Repo: https://github.com/TU_USUARIO/sonic-finder

🛠️ Stack:
• Python 3.13 + FastAPI
• scikit-learn (K-NN + Cosine Similarity)
• Google Cloud Run
• 114K Spotify tracks

🎯 Features:
• Búsqueda por similitud de audio
• Visualización de espacio vectorial (PCA)
• Comparación de features (radar charts)
• 12 recomendaciones personalizadas

#MachineLearning #Python #AI #DataScience #CloudRun
```

---

## ❓ FAQ

### ¿Por qué los modelos están en GitHub?
Los archivos son <20MB c/u (dentro del límite de GitHub). Necesarios para deployment.

### ¿Cómo actualizar el dataset?
```bash
python download_dataset.py  # Descarga nuevo dataset
# Rebuild modelo si es necesario
git add data/ artifacts/
git commit -m "chore: update dataset"
git push
./deploy-cloudrun.sh
```

### ¿Cómo cambiar la región de Cloud Run?
Edita `deploy-cloudrun.sh`, cambia `us-central1` por tu región preferida.

### ¿Cuánto cuesta?
Free tier incluye 2M requests/mes. Para demos/portfolio: **$0-2/mes**.

---

🎉 ¡Listo para producción!
