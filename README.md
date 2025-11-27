# 🎵 Sonic Finder - AI Music Recommender

Sistema de recomendación de música **Content-Based** con **interfaz web moderna** y **API REST**, usando **scikit-learn K-NN con similitud del coseno** para búsqueda precisa sobre 114,000 canciones de Spotify.

**Stack completo**: FastAPI + Landing Page interactiva + Docker + Google Cloud Run ready

---

## ✨ Features

- 🎯 **Recomendaciones precisas** basadas en 10 características de audio
- ⚡ **Búsqueda exacta** (< 1ms) con K-Nearest Neighbors + Cosine Similarity
- 🎨 **Landing page moderna** con visualización de espacio vectorial (PCA)
- 🔍 **Autocompletado inteligente** en tiempo real
- 📊 **Comparación de features** con radar charts interactivos
- 📡 **API REST completa** con 7 endpoints y documentación interactiva
- 🐳 **Docker ready** para despliegue en Google Cloud Run
- 🎵 **114,000+ canciones** de Spotify indexadas

---

## 🏗️ Arquitectura

```
sonic-finder/
├── recommenders/
│   ├── __init__.py
│   └── sklearn_recommender.py   # Motor K-NN (sklearn)
├── api/
│   ├── __init__.py
│   ├── models.py                # Pydantic models
│   └── routes.py                # 7 API endpoints
├── templates/
│   └── index.html               # Landing page (Sonic Finder)
├── static/
│   ├── css/styles.css           # Estilos con animaciones
│   ├── js/app.js                # Frontend + Chart.js
│   └── images/                  # EDA visualizations
├── data/                        # Dataset de Spotify (19MB)
│   └── spotify_tracks.csv
├── artifacts/                   # Modelos ML (8.7MB)
│   ├── sklearn_model.pkl        # Modelo K-NN
│   └── scaler.pkl               # StandardScaler
├── main.py                      # FastAPI application
├── Dockerfile                   # Container config (Python 3.13)
├── deploy-cloudrun.sh           # Script deployment GCP
├── run_local.sh                 # Servidor local
├── requirements.txt             # Dependencias
└── README.md
```

---

## 🚀 Quick Start

### Opción 1: Inicio automático (Recomendado)

```bash
# El script descargará el dataset automáticamente si no existe
chmod +x run_local.sh
./run_local.sh
```

El dataset se descarga automáticamente desde Hugging Face (114K tracks).

Abre tu navegador en: **http://localhost:8080**

### Opción 2: Descarga manual del dataset

```bash
# Descargar dataset primero
python download_dataset.py

# Luego ejecutar servidor
./run_local.sh
```

### Opción 3: Manual completo

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Acceso a la aplicación

- 🌐 **Landing Page**: http://localhost:8080
- 📚 **API Docs (Swagger)**: http://localhost:8080/docs
- 📖 **ReDoc**: http://localhost:8080/redoc
- ❤️ **Health Check**: http://localhost:8080/health

---

## 📊 Features de Audio Utilizadas

El sistema utiliza 10 características de audio de Spotify:

1. **danceability** - Qué tan bailable es la canción
2. **energy** - Intensidad y actividad
3. **loudness** - Volumen en dB
4. **speechiness** - Presencia de palabras habladas
5. **acousticness** - Confianza de que es acústica
6. **instrumentalness** - Predicción de ausencia de voz
7. **liveness** - Presencia de audiencia
8. **valence** - Positividad musical
9. **tempo** - BPM estimado
10. **duration_ms** - Duración en milisegundos

---

---

## 🌐 Uso de la Web App

### Interfaz Web (Sonic Finder)

1. Abre http://localhost:8080 en tu navegador
2. Escribe el nombre de una canción en el buscador
3. Selecciona de las sugerencias de autocompletado
4. ¡Obtén 10 recomendaciones similares instantáneamente!

**Features de la interfaz:**
- Búsqueda con autocompletado en tiempo real
- Visualización de ondas de audio animadas
- Tarjetas de recomendación con scores de similitud
- Diseño responsivo y moderno
- Quick suggestions para exploración rápida

---

## 🔌 API REST

### Endpoints disponibles

#### 1. Obtener Recomendaciones

```bash
POST /api/recommend
Content-Type: application/json

{
  "track_name": "Bohemian Rhapsody",
  "n": 10
}
```

#### 2. Búsqueda de Canciones (Autocomplete)

```bash
GET /api/search?q=bohemian&limit=10
```

#### 3. Recomendaciones por Features Personalizadas

```bash
POST /api/recommend-by-features
Content-Type: application/json

{
  "danceability": 0.7,
  "energy": 0.8,
  "loudness": -5.0,
  "speechiness": 0.1,
  "acousticness": 0.2,
  "instrumentalness": 0.0,
  "liveness": 0.3,
  "valence": 0.9,
  "tempo": 120.0,
  "duration_ms": 200000,
  "n": 10
}
```

#### 4. Canciones Aleatorias

```bash
GET /api/random?n=5
```

**Documentación interactiva**: http://localhost:8080/docs

---

## 🔧 Uso Programático (Python SDK)

### 1. Entrenar el Modelo (Una sola vez)

```python
import pandas as pd
from recommenders import SklearnRecommender

# Cargar dataset
df = pd.read_csv('data/spotify_tracks.csv')

# Inicializar y entrenar modelo
recommender = SklearnRecommender(df)
recommender.fit_and_save_model(
    model_path='artifacts/sklearn_model.pkl',
    scaler_path='artifacts/scaler.pkl'
)
```

### 2. Cargar Modelo Pre-entrenado (Producción)

```python
# Cargar dataset y modelo
df = pd.read_csv('data/spotify_tracks.csv')
recommender = SklearnRecommender(df)

recommender.load_model(
    model_path='artifacts/sklearn_model.pkl',
    scaler_path='artifacts/scaler.pkl'
)
```

### 3. Obtener Recomendaciones

```python
# Por nombre de canción
recommendations = recommender.get_recommendations(
    track_name="Bohemian Rhapsody",
    n=10
)

print(recommendations)
# Output:
#           track_name              artists  track_genre  similarity_score
# 0  Don't Stop Me Now               Queen         rock           0.95
# 1    We Will Rock You              Queen         rock           0.93
# ...
```

### 4. Query con Vector de Features Personalizado

```python
import numpy as np

# [danceability, energy, loudness, ..., duration_ms]
custom_features = np.array([0.7, 0.8, -5.0, 0.1, 0.2, 0.0, 0.3, 0.9, 120.0, 200000])

recommendations = recommender.get_recommendations_by_features(
    feature_vector=custom_features,
    n=5
)
```

---

## 🎯 Parámetros Clave

### `fit_and_save_model()`

- **`model_path`**: Ruta para guardar el modelo K-NN entrenado
- **`scaler_path`**: Ruta para guardar el StandardScaler

### `get_recommendations()`

- **`track_name`**: Nombre de la canción semilla
- **`n`**: Número de recomendaciones (default: 10)

### `get_recommendations_by_features()`

- **`feature_vector`**: Vector de 10 features de audio
- **`n`**: Número de recomendaciones (default: 10)

---

## 📈 Métricas de Similaridad

El sistema usa **similitud del coseno** de sklearn, convertida a **similarity score**:

```python
# Cosine similarity ranges from -1 to 1
# We normalize it to 0-1 scale
similarity_score = (cosine_similarity + 1) / 2
```

- **1.0** = Idénticas (coseno = 1)
- **0.5** = Perpendiculares (coseno = 0)
- **0.0** = Completamente opuestas (coseno = -1)

---

## 🐳 Despliegue en Google Cloud Run

### Build local con Docker

```bash
# Build imagen
docker build -t spotify-recommender .

# Run localmente
docker run -p 8080:8080 spotify-recommender
```

### Deploy en GCP

```bash
# Usar script de deployment automático
./deploy-cloudrun.sh
```

**Ver guía completa**: [DEPLOYMENT.md](DEPLOYMENT.md)

### Configuración Cloud Run recomendada

- **Memory**: 2 GiB
- **CPU**: 2 vCPU
- **Timeout**: 300s
- **Min instances**: 1 (evita cold starts)
- **Max instances**: 10

---

## ⚡ Performance

- **Entrenamiento del modelo**: ~10-20 segundos (114k canciones)
- **Búsqueda**: **< 1ms** por query
- **Tamaño del modelo**: ~8.7 MB (sklearn_model.pkl)
- **RAM en producción**: ~500 MB

---

## 📚 Referencias

- [scikit-learn NearestNeighbors](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html)
- [Spotify Web API - Audio Features](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)

---

## 🛠️ Troubleshooting

### Error: "Track not found"
- Verifica que el nombre esté exactamente en el dataset
- La búsqueda es case-insensitive
- Usa `df['track_name'].unique()` para ver nombres disponibles

### Error: "Model not loaded"
- Llama `fit_and_save_model()` o `load_model()` primero

### Performance lenta
- Verifica que el modelo esté correctamente cargado
- El modelo K-NN usa búsqueda exacta, siempre rápida (< 1ms)

---

---

## 🎨 Diseño de la Interfaz

**Sonic Finder** presenta una estética moderna de **visualización de audio**:

- **Tema oscuro** con acentos neón (verde lima, azul eléctrico, púrpura)
- **Ondas de audio animadas** en el fondo
- **Tipografía distintiva**: Orbitron (display) + DM Sans (cuerpo)
- **Glassmorphism** y efectos de glow
- **Animaciones fluidas** con stagger effects
- **Micro-interacciones** responsivas

---

## 📦 Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno y rápido
- **scikit-learn** - K-Nearest Neighbors + StandardScaler
- **Pandas** - Manipulación de datos
- **Pydantic** - Validación de datos

### Frontend
- **HTML5 + CSS3** - Estructura y estilos
- **JavaScript (Vanilla)** - Lógica del cliente
- **Google Fonts** - Orbitron & DM Sans
- **CSS Animations** - Efectos visuales fluidos

### DevOps
- **Docker** - Containerización
- **Google Cloud Build** - CI/CD
- **Google Cloud Run** - Serverless deployment
- **Uvicorn** - ASGI server

---

## 📈 Performance Metrics

- **Model Training Time**: ~10-20 segundos (114K tracks)
- **Query Speed**: **< 1ms** por búsqueda
- **Model Size**: ~8.7 MB (sklearn_model.pkl)
- **Memory Usage**: ~500 MB en producción
- **Cold Start**: ~5-10s (carga del modelo)
- **API Response Time**: ~50-100ms (incluye red)

---

## 🤝 Contribuciones

Mejoras bienvenidas:

1. Fork el repositorio
2. Crea una branch (`git checkout -b feature/nueva-feature`)
3. Commit cambios (`git commit -m 'Agrega nueva feature'`)
4. Push a la branch (`git push origin feature/nueva-feature`)
5. Abre un Pull Request

---

## 📄 Licencia

MIT License - Ver LICENSE para más detalles

---

## 🎯 Roadmap

- [ ] Filtros avanzados (por género, año, popularidad)
- [ ] Playlist generation automática
- [ ] Integración con Spotify API para reproducción
- [ ] Sistema de favoritos y historial
- [ ] A/B testing de algoritmos
- [ ] Modo de exploración por features
- [ ] Export de recomendaciones a CSV/JSON
- [ ] Dashboard de analytics
# recommender-system
