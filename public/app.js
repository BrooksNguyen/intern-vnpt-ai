document.addEventListener('DOMContentLoaded', () => {
    // --- View Navigation Logic ---
    const navHome = document.getElementById('nav-home');
    const navLaunchBtn = document.getElementById('nav-launch-btn');
    const heroLaunchBtn = document.getElementById('hero-launch-btn');
    
    const landingView = document.getElementById('landing-view');
    const dashboardView = document.getElementById('dashboard-view');

    function showDashboard() {
        landingView.classList.remove('active');
        setTimeout(() => {
            landingView.style.display = 'none';
            dashboardView.style.display = 'block';
            // Trigger reflow
            void dashboardView.offsetWidth;
            dashboardView.classList.add('active');
            window.scrollTo(0, 0);
            
            // Fetch stats when dashboard is opened
            if(!window.dashboardInitialized) {
                initDashboard();
                window.dashboardInitialized = true;
            }
        }, 400); // Wait for fade out
    }

    function showLanding() {
        dashboardView.classList.remove('active');
        setTimeout(() => {
            dashboardView.style.display = 'none';
            landingView.style.display = 'block';
            void landingView.offsetWidth;
            landingView.classList.add('active');
            window.scrollTo(0, 0);
        }, 400);
    }

    navLaunchBtn.addEventListener('click', showDashboard);
    heroLaunchBtn.addEventListener('click', showDashboard);
    navHome.addEventListener('click', showLanding);


    // --- Dashboard Logic ---
    const API_BASE = '/api';

    const statusBadge = document.getElementById('api-status');
    const statusText = statusBadge.querySelector('.status-text');
    const roomsVal = document.getElementById('rooms-val');
    const msgsVal = document.getElementById('msgs-val');
    
    const roomSelect = document.getElementById('room-select');
    const loadBtn = document.getElementById('load-btn');
    const chatContainer = document.getElementById('chat-container');
    
    let pollInterval = null;
    let sentimentTrendChartInstance = null;

    // --- Tab Switching Logic ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
        });
    });

    // --- Utility: Animated Counter ---
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString();
            if (progress < 1) window.requestAnimationFrame(step);
        };
        window.requestAnimationFrame(step);
    }

    async function initDashboard() {
        initPipelineMonitor();
    }

    // --- Pipeline Monitor Mock (Tab 2) ---
    let pipeInterval;
    let pipeThroughputChart, pipeLatencyChart;
    const throughputData = Array(20).fill(400);
    const latencyData = Array(10).fill(0).map((_, i) => ({ x: i*10, y: Math.random()*50 }));
    let totalIngested = 1284920;

    function initPipelineMonitor() {
        // Initialize charts
        const ctxT = document.getElementById('pipeThroughputChart');
        if (ctxT) {
            pipeThroughputChart = new Chart(ctxT.getContext('2d'), {
                type: 'line',
                data: {
                    labels: Array(20).fill(''),
                    datasets: [{
                        label: 'Messages/sec',
                        data: throughputData,
                        borderColor: '#0ea5e9',
                        backgroundColor: 'rgba(14, 165, 233, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, color: '#94a3b8', scales: { x: { display: false }, y: { min: 200, max: 800, grid: { color: '#334155' } } }, plugins: { legend: { display: false } } }
            });
        }

        const ctxL = document.getElementById('pipeLatencyChart');
        if (ctxL) {
            pipeLatencyChart = new Chart(ctxL.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: Array(10).fill('').map((_, i) => `${i*5}ms`),
                    datasets: [{
                        label: 'Requests',
                        data: latencyData.map(d => d.y),
                        backgroundColor: '#8b5cf6',
                        borderRadius: 4
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, color: '#94a3b8', scales: { x: { grid: { display: false }, ticks: { color: '#94a3b8' } }, y: { display: false } }, plugins: { legend: { display: false } } }
            });
        }

        // Start interval
        if (pipeInterval) clearInterval(pipeInterval);
        pipeInterval = setInterval(updatePipelineTick, 2000);
    }

    function updatePipelineTick() {
        if (document.getElementById('tab-pipeline').style.display === 'none') return;

        const currentTps = Math.floor(400 + Math.random() * 200);
        totalIngested += (currentTps * 2);
        const currentLat = Math.floor(25 + Math.random() * 30);

        // Update KPIs
        document.getElementById('pipe-ingested').innerText = totalIngested.toLocaleString();
        document.getElementById('pipe-throughput').innerHTML = `${currentTps} <span style="font-size:0.5em;color:var(--text-muted)">msgs/s</span>`;
        document.getElementById('pipe-latency').innerHTML = `${currentLat} <span style="font-size:0.5em;color:var(--text-muted)">ms</span>`;

        // Update Flow Rates
        document.getElementById('flow-rate-1').innerText = `${currentTps}/s`;
        document.getElementById('flow-rate-2').innerText = `${currentTps - Math.floor(Math.random()*10)}/s`;
        document.getElementById('flow-rate-3').innerText = `${Math.floor(currentTps / 20)}/s`;
        
        const sparkStatus = document.getElementById('flow-status-spark');
        if (sparkStatus) {
            sparkStatus.style.color = currentTps > 550 ? '#f59e0b' : '#10b981';
            sparkStatus.innerText = currentTps > 550 ? '● High Load' : '● Processing';
        }

        // Update Charts
        if (pipeThroughputChart) {
            throughputData.shift();
            throughputData.push(currentTps);
            pipeThroughputChart.update('none');
        }

        if (pipeLatencyChart) {
            const newLat = Array(10).fill(0).map(() => Math.random() * (currentTps > 550 ? 100 : 50));
            pipeLatencyChart.data.datasets[0].data = newLat;
            pipeLatencyChart.update('none');
        }

        // Update Logs
        const logsContainer = document.getElementById('terminal-logs');
        if (logsContainer) {
            const msgTypes = [
                `[INFO] Batch #${Math.floor(Math.random()*10000)} committed to ScyllaDB: ${currentTps} rows in ${currentLat}ms`,
                `[SUCCESS] Health check passed: Cluster latency ${currentLat-10}ms`,
                `[INFO] Partition compaction completed on Node-${Math.floor(Math.random()*3)+1}`,
                currentTps > 550 ? `[WARN] High throughput detected: Auto-scaling Spark workers...` : `[INFO] Kafka offset committed successfully.`
            ];
            
            const logLine = document.createElement('div');
            const msg = msgTypes[Math.floor(Math.random() * msgTypes.length)];
            logLine.innerText = `> ${new Date().toISOString().split('T')[1].slice(0,-1)} - ${msg}`;
            if (msg.includes('[WARN]')) logLine.style.color = '#f59e0b';
            
            logsContainer.appendChild(logLine);
            if (logsContainer.children.length > 50) logsContainer.removeChild(logsContainer.firstChild);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }


    // --- Kaggle Universal Analyzer (Tab 1) ---
    const kaggleBtn = document.getElementById('kaggle-btn');
    const kaggleSlug = document.getElementById('kaggle-slug');
    const kaggleColumn = document.getElementById('kaggle-column');
    
    // Chips integration
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            kaggleSlug.value = chip.dataset.slug;
            kaggleColumn.value = '';
            kaggleBtn.click();
        });
    });

    // Store all dynamic chart instances for cleanup
    let kaggleChartInstances = [];

    function destroyAllKaggleCharts() {
        kaggleChartInstances.forEach(c => { try { c.destroy(); } catch(e) {} });
        kaggleChartInstances = [];
    }

    /**
     * Render KPI cards dynamically from the universal profile.
     */
    function renderKPIs(profile) {
        const strip = document.getElementById('kaggle-kpi-strip');
        const cols = profile.columns || {};
        const colTypes = {};
        Object.values(cols).forEach(c => { colTypes[c.type] = (colTypes[c.type] || 0) + 1; });
        const typeStr = Object.entries(colTypes).map(([k,v]) => `${v} ${k}`).join(', ');

        strip.innerHTML = `
            <div class="metric-card small"><div class="metric-label">File</div><div class="metric-value-text">${profile.csv_analyzed || '--'}</div></div>
            <div class="metric-card small"><div class="metric-label">Dimensions</div><div class="metric-value-text">${(profile.total_rows || 0).toLocaleString()} × ${profile.total_cols || 0}</div></div>
            <div class="metric-card small"><div class="metric-label">Column Types</div><div class="metric-value-text">${typeStr || '--'}</div></div>
            <div class="metric-card small"><div class="metric-label">Data Health</div><div class="metric-value-text">${profile.missing_rate ?? '--'}% Missing</div></div>
        `;
    }

    /**
     * Render a compact column summary table.
     */
    function renderColumnTable(profile) {
        const container = document.getElementById('kaggle-column-table');
        const cols = profile.columns || {};
        const colNames = profile.column_names || Object.keys(cols);
        if (colNames.length === 0) { container.innerHTML = ''; return; }

        let rows = colNames.map(name => {
            const info = cols[name] || {};
            let detail = '';
            if (info.type === 'numeric') {
                const s = info.stats || {};
                detail = `mean=${s.mean ?? '?'}, std=${s.std ?? '?'}`;
            } else if (info.type === 'categorical') {
                detail = `${info.unique_count ?? '?'} unique`;
            } else if (info.type === 'text') {
                detail = `avg len=${Math.round(info.avg_length || 0)}`;
            } else if (info.type === 'datetime') {
                const s = info.stats || {};
                detail = `${s.range_days ?? '?'} days`;
            }
            const missBadge = (info.missing_pct || 0) > 5
                ? `<span style="color:#ef4444">${info.missing_pct}%</span>`
                : `<span style="color:#22c55e">${info.missing_pct ?? 0}%</span>`;
            return `<tr><td style="font-weight:600;color:#f8fafc">${name}</td><td><span class="col-type-badge ${info.type}">${info.type || '?'}</span></td><td>${missBadge}</td><td style="color:#94a3b8">${detail}</td></tr>`;
        }).join('');

        container.innerHTML = `
            <table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
                <thead><tr style="border-bottom:1px solid #334155;text-transform:uppercase;font-size:0.7rem;color:#94a3b8;letter-spacing:0.5px;">
                    <th style="text-align:left;padding:0.5rem">Column</th>
                    <th style="text-align:left;padding:0.5rem">Type</th>
                    <th style="text-align:left;padding:0.5rem">Missing</th>
                    <th style="text-align:left;padding:0.5rem">Summary</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
    }

    /**
     * Universal Chart Renderer: takes an array of chart configs and
     * dynamically creates Chart.js canvases inside the grid.
     */
    function renderDynamicCharts(chartConfigs) {
        destroyAllKaggleCharts();
        const grid = document.getElementById('kaggle-charts-grid');
        grid.innerHTML = '';

        // Adjust grid columns based on number of charts
        if (chartConfigs.length === 1) grid.style.gridTemplateColumns = '1fr';
        else if (chartConfigs.length === 3) grid.style.gridTemplateColumns = '1fr 1fr';
        else grid.style.gridTemplateColumns = '1fr 1fr';

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = '#334155';

        chartConfigs.forEach((cfg, i) => {
            const card = document.createElement('div');
            card.className = 'chart-card';
            card.style.opacity = '0';
            card.style.animation = `fadeIn 0.4s ease forwards ${i * 0.1}s`;

            const title = document.createElement('h4');
            title.textContent = cfg.title || `Chart ${i + 1}`;
            card.appendChild(title);

            const wrapper = document.createElement('div');
            wrapper.className = 'chart-wrapper';
            const canvas = document.createElement('canvas');
            canvas.id = `kaggle-dyn-chart-${i}`;
            wrapper.appendChild(canvas);
            card.appendChild(wrapper);
            grid.appendChild(card);

            try {
                const chartOptions = Object.assign({
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#cbd5e1' } } }
                }, cfg.options || {});

                const instance = new Chart(canvas.getContext('2d'), {
                    type: cfg.type || 'bar',
                    data: cfg.data,
                    options: chartOptions,
                });
                kaggleChartInstances.push(instance);
            } catch (err) {
                console.error(`Chart ${i} render error:`, err);
                wrapper.innerHTML = `<p style="color:#ef4444;text-align:center;padding:2rem">Chart render error</p>`;
            }
        });
    }

    // ---- Main Analyze Button Handler ----
    kaggleBtn.addEventListener('click', async () => {
        let slug = kaggleSlug.value.trim();
        if (!slug) return alert('Please enter a valid Kaggle Dataset Slug');

        // Auto-extract slug from full Kaggle URL
        try {
            if (slug.includes('kaggle.com/datasets/')) {
                const urlObj = new URL(slug);
                const pathParts = urlObj.pathname.split('/').filter(Boolean);
                if (pathParts.length >= 3) slug = `${pathParts[1]}/${pathParts[2]}`;
            }
        } catch (e) {}

        // Reset UI
        kaggleBtn.innerText = 'Analyzing...'; kaggleBtn.disabled = true;
        document.getElementById('kaggle-empty-state').style.display = 'none';
        document.getElementById('kaggle-error').style.display = 'none';
        
        const resultsContainer = document.getElementById('kaggle-results-container');
        const loadingIndicator = document.getElementById('kaggle-loading');
        
        if (resultsContainer.style.display !== 'none') {
            resultsContainer.style.opacity = '0';
            resultsContainer.style.transition = 'opacity 0.3s ease';
            await new Promise(r => setTimeout(r, 300));
        }
        
        resultsContainer.style.display = 'none';
        loadingIndicator.style.display = 'block';

        let url = `${API_BASE}/analyze/kaggle?dataset=${encodeURIComponent(slug)}`;
        if (kaggleColumn.value.trim()) url += `&text_column=${encodeURIComponent(kaggleColumn.value.trim())}`;

        try {
            // ---- Step 1: Get universal data profile ----
            const res = await fetch(url);
            const contentType = res.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await res.text();
                if (text.includes("<!DOCTYPE html>") || text.includes("<html")) {
                    if (res.status === 502 || res.status === 503) {
                        throw new Error("Backend is waking up (Cold Start). Please wait 30-60s and retry.");
                    }
                    throw new Error(`Backend returned HTML instead of JSON (Status ${res.status}).`);
                }
                throw new Error(`Unexpected response format (Status ${res.status})`);
            }

            let profile;
            try { profile = await res.json(); } catch (err) { throw new Error('Failed to parse profile JSON'); }
            if (!res.ok) throw new Error(profile.detail || 'Analysis failed');

            // Show warning if using mock data
            if (profile.error && profile.error !== 'None') {
                document.getElementById('kaggle-error').innerText = `⚠ ${profile.error} — Showing mock data`;
                document.getElementById('kaggle-error').style.display = 'block';
            }

            // ---- Step 2: Render profile KPIs ----
            loadingIndicator.style.display = 'none';
            resultsContainer.style.opacity = '0';
            resultsContainer.style.display = 'block';
            
            // Trigger reflow to ensure transition works
            void resultsContainer.offsetWidth;
            
            resultsContainer.style.transition = 'opacity 0.5s ease';
            resultsContainer.style.opacity = '1';
            
            renderKPIs(profile);
            // We purposely do NOT render the column table anymore based on user feedback

            // ---- Step 3: Request AI chart configs + narrative ----
            const aiContainer = document.getElementById('kaggle-ai-feedback');
            const aiContent = document.getElementById('kaggle-ai-content');
            aiContainer.style.display = 'block';
            aiContent.innerHTML = '<div style="display:flex;align-items:center;gap:0.5rem"><div class="spinner" style="width:16px;height:16px;border-width:2px"></div> Generating AI-powered visualizations & analysis...</div>';
            setTimeout(() => { aiContainer.style.opacity = '1'; }, 50);

            try {
                const aiRes = await fetch(`${API_BASE}/analyze/ai-feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile })
                });
                const aiData = await aiRes.json();

                // Render charts (from AI or fallback)
                if (aiData.charts && aiData.charts.length > 0) {
                    renderDynamicCharts(aiData.charts);
                }

                // Render narrative
                if (aiData.narrative) {
                    const formatted = aiData.narrative
                        .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#fff">$1</strong>')
                        .replace(/\n/g, '<br>');
                    aiContent.innerHTML = formatted;
                    if (aiData.ai_error) {
                        document.getElementById('ai-card-title').textContent = 'Data Analysis (Rule-Based Fallback)';
                    } else {
                        document.getElementById('ai-card-title').textContent = 'Gemini AI Data Analyst';
                    }
                } else {
                    aiContent.innerHTML = '<span style="color:#f59e0b">AI returned no narrative. Charts rendered from heuristics.</span>';
                }
            } catch (err) {
                // If AI fails, still show something useful
                aiContent.innerHTML = '<span style="color:#f59e0b">AI Insights unavailable. Charts generated with heuristics.</span>';
                console.error('AI feedback error:', err);
            }

        } catch (error) {
            document.getElementById('kaggle-loading').style.display = 'none';
            document.getElementById('kaggle-error').innerText = `Error: ${error.message}`;
            document.getElementById('kaggle-error').style.display = 'block';
        } finally {
            kaggleBtn.innerText = 'Analyze'; kaggleBtn.disabled = false;
        }
    });

});

