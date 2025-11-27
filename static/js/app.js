/**
 * Sonic Finder - Frontend Application
 * Handles search, autocomplete, and recommendations display
 */

// ========================================
// STATE MANAGEMENT
// ========================================

const state = {
    searchTimeout: null,
    selectedIndex: -1,
    currentResults: []
};

// ========================================
// DOM ELEMENTS
// ========================================

const elements = {
    searchInput: document.getElementById('trackSearch'),
    searchLoader: document.getElementById('searchLoader'),
    autocompleteDropdown: document.getElementById('autocompleteDropdown'),
    resultsSection: document.getElementById('resultsSection'),
    recommendationsGrid: document.getElementById('recommendationsGrid'),
    seedTrack: document.getElementById('seedTrack'),
    resetBtn: document.getElementById('resetBtn'),
    suggestionChips: document.querySelectorAll('.suggestion-chip')
};

// ========================================
// API CALLS
// ========================================

const API = {
    async searchTracks(query) {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`);
        if (!response.ok) throw new Error('Search failed');
        return await response.json();
    },

    async getRecommendations(trackName) {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ track_name: trackName, n: 20 })  // Request more to filter duplicates
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get recommendations');
        }

        return await response.json();
    },

    async getVectorData(trackName) {
        const response = await fetch('/api/recommend/vectors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ track_name: trackName, n: 12 })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get vector data');
        }

        return await response.json();
    },

    async getRandomTracks(n = 5) {
        const response = await fetch(`/api/random?n=${n}`);
        if (!response.ok) throw new Error('Failed to get random tracks');
        return await response.json();
    }
};

// ========================================
// SEARCH & AUTOCOMPLETE
// ========================================

function handleSearchInput(e) {
    const query = e.target.value.trim();

    // Clear previous timeout
    if (state.searchTimeout) {
        clearTimeout(state.searchTimeout);
    }

    // Hide dropdown if query is empty
    if (query.length === 0) {
        hideAutocomplete();
        return;
    }

    // Debounce search
    state.searchTimeout = setTimeout(() => {
        performSearch(query);
    }, 300);
}

async function performSearch(query) {
    try {
        showLoader();
        const data = await API.searchTracks(query);
        displayAutocomplete(data.matches);
        hideLoader();
    } catch (error) {
        console.error('Search error:', error);
        hideLoader();
        showError('Error buscando canciones');
    }
}

function displayAutocomplete(matches) {
    if (matches.length === 0) {
        hideAutocomplete();
        return;
    }

    state.currentResults = matches;
    state.selectedIndex = -1;

    elements.autocompleteDropdown.innerHTML = matches
        .map((track, index) => `
            <div class="autocomplete-item" data-index="${index}" data-track="${track}">
                ${track}
            </div>
        `)
        .join('');

    elements.autocompleteDropdown.classList.add('active');

    // Add click listeners
    document.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
            selectTrack(item.dataset.track);
        });
    });
}

function hideAutocomplete() {
    elements.autocompleteDropdown.classList.remove('active');
    state.currentResults = [];
    state.selectedIndex = -1;
}

function showLoader() {
    elements.searchLoader.classList.add('active');
}

function hideLoader() {
    elements.searchLoader.classList.remove('active');
}

// ========================================
// KEYBOARD NAVIGATION
// ========================================

function handleKeydown(e) {
    const items = document.querySelectorAll('.autocomplete-item');

    if (!elements.autocompleteDropdown.classList.contains('active')) {
        return;
    }

    switch (e.key) {
        case 'ArrowDown':
            e.preventDefault();
            state.selectedIndex = Math.min(state.selectedIndex + 1, items.length - 1);
            updateSelection(items);
            break;

        case 'ArrowUp':
            e.preventDefault();
            state.selectedIndex = Math.max(state.selectedIndex - 1, -1);
            updateSelection(items);
            break;

        case 'Enter':
            e.preventDefault();
            if (state.selectedIndex >= 0) {
                selectTrack(state.currentResults[state.selectedIndex]);
            } else if (state.currentResults.length > 0) {
                selectTrack(state.currentResults[0]);
            }
            break;

        case 'Escape':
            hideAutocomplete();
            break;
    }
}

function updateSelection(items) {
    items.forEach((item, index) => {
        if (index === state.selectedIndex) {
            item.classList.add('selected');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('selected');
        }
    });
}

// ========================================
// RECOMMENDATIONS
// ========================================

async function selectTrack(trackName) {
    try {
        hideAutocomplete();
        elements.searchInput.value = trackName;
        showLoader();

        // Fetch both recommendations and vector data in parallel
        const [data, vectorData] = await Promise.all([
            API.getRecommendations(trackName),
            API.getVectorData(trackName)
        ]);

        displayRecommendations(data, vectorData);

        hideLoader();
    } catch (error) {
        console.error('Recommendation error:', error);
        hideLoader();
        showError(error.message || 'Error obteniendo recomendaciones');
    }
}

function displayRecommendations(data, vectorData) {
    // Update seed track
    elements.seedTrack.textContent = data.seed_track;

    // Create vector plot
    createVectorPlot(vectorData);

    // Remove duplicates based on track_name and artists
    const uniqueRecommendations = [];
    const seen = new Set();

    for (const track of data.recommendations) {
        const key = `${track.track_name}|${track.artists}`;
        if (!seen.has(key)) {
            seen.add(key);
            uniqueRecommendations.push(track);
        }
        if (uniqueRecommendations.length === 12) break;
    }

    // Render recommendations with all 4 feature display options
    elements.recommendationsGrid.innerHTML = uniqueRecommendations
        .map((track, index) => {
            // Calculate top 3 contributing features
            const topFeatures = getTopContributingFeatures(track, data.seed_track_features);

            return `
            <div class="recommendation-card" style="animation-delay: ${index * 0.05}s">
                <div class="card-header">
                    <div class="track-info">
                        <div class="track-name">${escapeHtml(track.track_name)}</div>
                        <div class="track-artists">${escapeHtml(track.artists)}</div>
                    </div>
                    <div class="similarity-badge">
                        ${(track.similarity_score * 100).toFixed(1)}%
                    </div>
                </div>
                ${track.track_genre ? `<span class="track-genre">${escapeHtml(track.track_genre)}</span>` : ''}

                <!-- Option 3: Top 3 Contributing Features -->
                <div class="top-features">
                    <div class="top-features-title">Top Similarities:</div>
                    <div class="top-features-list">
                        ${topFeatures.map(f => `
                            <div class="feature-chip">
                                <span class="feature-name">${f.name}</span>
                                <span class="feature-similarity">${f.similarity}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Option 2: Radar Chart Button -->
                <button class="radar-btn" onclick="showRadarChart(${index}, '${escapeHtml(track.track_name)}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                    Ver Comparación
                </button>

                <!-- Option 4: Expandable Panel -->
                <div class="features-toggle" onclick="toggleFeatures(${index})">
                    <span>Ver todas las características</span>
                    <svg class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                <div class="features-panel" id="features-panel-${index}">
                    <!-- Option 1: All Features Display -->
                    <div class="features-grid">
                        ${formatFeatureItem('Danceability', track.danceability, 0, 1)}
                        ${formatFeatureItem('Energy', track.energy, 0, 1)}
                        ${formatFeatureItem('Loudness', track.loudness, -60, 0)}
                        ${formatFeatureItem('Speechiness', track.speechiness, 0, 1)}
                        ${formatFeatureItem('Acousticness', track.acousticness, 0, 1)}
                        ${formatFeatureItem('Instrumentalness', track.instrumentalness, 0, 1)}
                        ${formatFeatureItem('Liveness', track.liveness, 0, 1)}
                        ${formatFeatureItem('Valence', track.valence, 0, 1)}
                        ${formatFeatureItem('Tempo', track.tempo, 0, 250, 'BPM')}
                        ${formatFeatureItem('Duration', track.duration_ms, 0, 600000, 'ms')}
                    </div>
                </div>
            </div>
            `;
        })
        .join('');

    // Store data for radar chart
    window.recommendationsData = data;

    // Show results section with smooth scroll
    elements.resultsSection.style.display = 'block';

    setTimeout(() => {
        elements.resultsSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
}

function createVectorPlot(vectorData) {
    console.log('Creating vector plot with data:', vectorData);

    // Get container directly
    const container = document.querySelector('.chart-wrapper');
    if (!container) {
        console.error('Chart wrapper not found!');
        return;
    }

    // Clear previous content but keep a placeholder
    container.innerHTML = '<div id="vector-plot-container" style="width: 100%; height: 400px;"></div>';

    const plotContainer = document.getElementById('vector-plot-container');
    const width = plotContainer.clientWidth || 800;
    const height = 400;

    console.log('Container dimensions:', width, height);
    const margin = { top: 20, right: 100, bottom: 40, left: 100 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.style.background = 'transparent';

    plotContainer.appendChild(svg);

    // Extract coordinates
    const vectors = vectorData.vectors;
    const xCoords = vectors.map(v => v.x);
    const yCoords = vectors.map(v => v.y);

    const xMin = Math.min(...xCoords, 0);
    const xMax = Math.max(...xCoords, 0);
    const yMin = Math.min(...yCoords, 0);
    const yMax = Math.max(...yCoords, 0);

    // Add padding
    const xPadding = (xMax - xMin) * 0.1;
    const yPadding = (yMax - yMin) * 0.1;

    // Scale functions
    const xScale = (x) => margin.left + ((x - (xMin - xPadding)) / (xMax - xMin + 2 * xPadding)) * plotWidth;
    const yScale = (y) => margin.top + plotHeight - ((y - (yMin - yPadding)) / (yMax - yMin + 2 * yPadding)) * plotHeight;

    // Origin point
    const originX = xScale(0);
    const originY = yScale(0);

    // Draw axes
    const axesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');

    // X-axis
    const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    xAxis.setAttribute('x1', margin.left);
    xAxis.setAttribute('y1', originY);
    xAxis.setAttribute('x2', width - margin.right);
    xAxis.setAttribute('y2', originY);
    xAxis.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
    xAxis.setAttribute('stroke-width', '1');
    axesGroup.appendChild(xAxis);

    // Y-axis
    const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    yAxis.setAttribute('x1', originX);
    yAxis.setAttribute('y1', margin.top);
    yAxis.setAttribute('x2', originX);
    yAxis.setAttribute('y2', height - margin.bottom);
    yAxis.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
    yAxis.setAttribute('stroke-width', '1');
    axesGroup.appendChild(yAxis);

    svg.appendChild(axesGroup);

    // Draw vectors
    vectors.forEach((vector, index) => {
        const x = xScale(vector.x);
        const y = yScale(vector.y);

        const isSeed = vector.is_seed;
        const color = isSeed ? '#00ff88' : interpolateColor(vector.similarity_score);

        // Draw arrow
        const arrow = createArrow(originX, originY, x, y, color, isSeed);
        svg.appendChild(arrow);

        // Draw point
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', x);
        circle.setAttribute('cy', y);
        circle.setAttribute('r', isSeed ? 6 : 4);
        circle.setAttribute('fill', color);
        circle.setAttribute('stroke', isSeed ? 'rgba(0, 255, 136, 0.5)' : 'rgba(255, 255, 255, 0.3)');
        circle.setAttribute('stroke-width', isSeed ? '3' : '1');
        circle.style.cursor = 'pointer';

        // Tooltip
        circle.addEventListener('mouseenter', (e) => {
            showVectorTooltip(e, vector);
        });
        circle.addEventListener('mouseleave', hideVectorTooltip);

        svg.appendChild(circle);

        // Label for all tracks
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', x + 10);
        label.setAttribute('y', y - 10);
        label.setAttribute('fill', isSeed ? '#00ff88' : '#00d4ff');
        label.setAttribute('font-family', isSeed ? 'Orbitron' : 'DM Sans');
        label.setAttribute('font-size', isSeed ? '12' : '10');
        label.setAttribute('font-weight', isSeed ? '700' : '500');
        label.textContent = vector.track_name;
        svg.appendChild(label);
    });

    // Add legend
    const legend = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    legend.setAttribute('x', width - margin.right + 10);
    legend.setAttribute('y', margin.top);
    legend.setAttribute('fill', 'rgba(255, 255, 255, 0.7)');
    legend.setAttribute('font-family', 'DM Sans');
    legend.setAttribute('font-size', '11');
    legend.textContent = `PCA: ${(vectorData.explained_variance[0] * 100).toFixed(1)}% + ${(vectorData.explained_variance[1] * 100).toFixed(1)}%`;
    svg.appendChild(legend);
}

function createArrow(x1, y1, x2, y2, color, isSeed) {
    const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');

    // Line
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('stroke', color);
    line.setAttribute('stroke-width', isSeed ? '2' : '1.5');
    line.setAttribute('stroke-opacity', isSeed ? '1' : '0.6');
    group.appendChild(line);

    // Simple arrowhead using polygon
    const dx = x2 - x1;
    const dy = y2 - y1;
    const angle = Math.atan2(dy, dx);
    const arrowSize = 8;

    const arrowX1 = x2 - arrowSize * Math.cos(angle - Math.PI / 6);
    const arrowY1 = y2 - arrowSize * Math.sin(angle - Math.PI / 6);
    const arrowX2 = x2 - arrowSize * Math.cos(angle + Math.PI / 6);
    const arrowY2 = y2 - arrowSize * Math.sin(angle + Math.PI / 6);

    const arrowhead = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    arrowhead.setAttribute('points', `${x2},${y2} ${arrowX1},${arrowY1} ${arrowX2},${arrowY2}`);
    arrowhead.setAttribute('fill', color);
    group.appendChild(arrowhead);

    return group;
}

function interpolateColor(similarity) {
    // Interpolate between purple (low) -> blue (mid) -> green (high)
    if (similarity >= 0.97) {
        return '#00ff88';  // Green
    } else if (similarity >= 0.95) {
        return '#00d4ff';  // Blue
    } else {
        return '#b026ff';  // Purple
    }
}

function showVectorTooltip(event, vector) {
    const tooltip = document.createElement('div');
    tooltip.id = 'vector-tooltip';
    tooltip.style.cssText = `
        position: fixed;
        background: rgba(10, 10, 10, 0.95);
        border: 1px solid #00ff88;
        color: #fff;
        padding: 12px;
        border-radius: 8px;
        pointer-events: none;
        z-index: 10000;
        font-family: 'DM Sans';
        font-size: 12px;
        max-width: 250px;
    `;

    tooltip.innerHTML = `
        <div style="color: #00ff88; font-family: 'Orbitron'; font-weight: 700; margin-bottom: 8px;">${vector.track_name}</div>
        <div style="margin-bottom: 4px;">Artista: ${vector.artists}</div>
        ${vector.track_genre ? `<div style="margin-bottom: 4px;">Género: ${vector.track_genre}</div>` : ''}
        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);">
            Similitud: ${(vector.similarity_score * 100).toFixed(2)}%
        </div>
    `;

    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY + 10) + 'px';

    document.body.appendChild(tooltip);
}

function hideVectorTooltip() {
    const tooltip = document.getElementById('vector-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function resetSearch() {
    elements.searchInput.value = '';
    elements.resultsSection.style.display = 'none';
    elements.recommendationsGrid.innerHTML = '';
    hideAutocomplete();

    // Clear vector plot
    const chartContainer = document.querySelector('.chart-wrapper');
    if (chartContainer) {
        chartContainer.innerHTML = '<canvas id="similarityChart"></canvas>';
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ========================================
// FEATURE DISPLAY UTILITIES
// ========================================

function getTopContributingFeatures(track, seedFeatures) {
    if (!seedFeatures) return [];

    const features = [
        { name: 'Danceability', track: track.danceability, seed: seedFeatures.danceability },
        { name: 'Energy', track: track.energy, seed: seedFeatures.energy },
        { name: 'Valence', track: track.valence, seed: seedFeatures.valence },
        { name: 'Acousticness', track: track.acousticness, seed: seedFeatures.acousticness },
        { name: 'Instrumentalness', track: track.instrumentalness, seed: seedFeatures.instrumentalness },
        { name: 'Liveness', track: track.liveness, seed: seedFeatures.liveness },
        { name: 'Speechiness', track: track.speechiness, seed: seedFeatures.speechiness }
    ];

    // Calculate similarity for each feature (inverse of absolute difference)
    const featureSimilarities = features.map(f => ({
        name: f.name,
        similarity: (100 - Math.abs(f.track - f.seed) * 100).toFixed(0)
    }));

    // Sort by similarity and return top 3
    return featureSimilarities
        .sort((a, b) => b.similarity - a.similarity)
        .slice(0, 3);
}

function formatFeatureItem(name, value, min, max, unit = '') {
    if (value === null || value === undefined) return '';

    const percentage = ((value - min) / (max - min)) * 100;
    const displayValue = unit === 'ms' ? (value / 1000).toFixed(1) + 's' :
                        unit ? value.toFixed(1) + unit :
                        value.toFixed(2);

    return `
        <div class="feature-item">
            <div class="feature-label">${name}</div>
            <div class="feature-bar">
                <div class="feature-fill" style="width: ${percentage}%"></div>
            </div>
            <div class="feature-value">${displayValue}</div>
        </div>
    `;
}

function toggleFeatures(index) {
    const panel = document.getElementById(`features-panel-${index}`);
    const toggle = panel.previousElementSibling;
    const icon = toggle.querySelector('.toggle-icon');

    if (panel.classList.contains('active')) {
        panel.classList.remove('active');
        icon.style.transform = 'rotate(0deg)';
    } else {
        panel.classList.add('active');
        icon.style.transform = 'rotate(180deg)';
    }
}

function showRadarChart(index, trackName) {
    const data = window.recommendationsData;
    if (!data || !data.seed_track_features) return;

    const track = data.recommendations[index];
    const seedFeatures = data.seed_track_features;

    // Create modal
    const modal = document.createElement('div');
    modal.id = 'radar-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.3s ease-out;
    `;

    modal.innerHTML = `
        <div style="background: var(--color-bg-card); border: 1px solid rgba(0, 255, 136, 0.2); border-radius: 16px; padding: 2rem; max-width: 600px; width: 90%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                <h3 style="color: #00ff88; font-family: 'Orbitron'; font-size: 1.5rem; margin: 0;">Comparación de Audio Features</h3>
                <button onclick="closeRadarModal()" style="background: none; border: none; color: #fff; font-size: 2rem; cursor: pointer; padding: 0; width: 40px; height: 40px;">&times;</button>
            </div>
            <div style="margin-bottom: 1rem; color: rgba(255,255,255,0.7); font-size: 0.9rem;">
                <div><strong style="color: #00ff88;">Seed:</strong> ${data.seed_track}</div>
                <div><strong style="color: #00d4ff;">Recommendation:</strong> ${trackName}</div>
            </div>
            <canvas id="radarChart" style="max-height: 400px;"></canvas>
        </div>
    `;

    document.body.appendChild(modal);

    // Create radar chart using Chart.js
    const ctx = document.getElementById('radarChart').getContext('2d');

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Danceability', 'Energy', 'Valence', 'Acousticness', 'Instrumentalness', 'Liveness', 'Speechiness'],
            datasets: [
                {
                    label: data.seed_track,
                    data: [
                        seedFeatures.danceability,
                        seedFeatures.energy,
                        seedFeatures.valence,
                        seedFeatures.acousticness,
                        seedFeatures.instrumentalness,
                        seedFeatures.liveness,
                        seedFeatures.speechiness
                    ],
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#00ff88',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#00ff88'
                },
                {
                    label: trackName,
                    data: [
                        track.danceability,
                        track.energy,
                        track.valence,
                        track.acousticness,
                        track.instrumentalness,
                        track.liveness,
                        track.speechiness
                    ],
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#00d4ff',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#00d4ff'
                }
            ]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        stepSize: 0.2,
                        color: 'rgba(255, 255, 255, 0.5)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        font: {
                            size: 12,
                            family: 'DM Sans'
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                        font: {
                            family: 'DM Sans',
                            size: 14
                        }
                    }
                }
            }
        }
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeRadarModal();
        }
    });
}

function closeRadarModal() {
    const modal = document.getElementById('radar-modal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => modal.remove(), 300);
    }
}

// Make functions globally available
window.toggleFeatures = toggleFeatures;
window.showRadarChart = showRadarChart;
window.closeRadarModal = closeRadarModal;

// ========================================
// UTILITY FUNCTIONS
// ========================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(255, 46, 151, 0.2);
        border: 1px solid rgba(255, 46, 151, 0.5);
        color: #ff2e97;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        backdrop-filter: blur(10px);
        z-index: 1000;
        animation: slideDown 0.3s ease-out;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========================================
// EVENT LISTENERS
// ========================================

elements.searchInput.addEventListener('input', handleSearchInput);
elements.searchInput.addEventListener('keydown', handleKeydown);
elements.resetBtn.addEventListener('click', resetSearch);

// Suggestion chips
elements.suggestionChips.forEach(chip => {
    chip.addEventListener('click', () => {
        const trackName = chip.dataset.track;
        selectTrack(trackName);
    });
});

// Click outside to close autocomplete
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-container')) {
        hideAutocomplete();
    }
});

// ========================================
// INITIALIZATION
// ========================================

console.log('🎵 Sonic Finder initialized');

// Prevent form submission on enter
elements.searchInput.form?.addEventListener('submit', (e) => {
    e.preventDefault();
});
