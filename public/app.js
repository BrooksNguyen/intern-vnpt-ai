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
        await fetchStats();
        await fetchRooms();
        renderMockSentimentTrend();
        
        // Setup Real-Time Polling for Pipeline monitor
        if (!pollInterval) {
            pollInterval = setInterval(async () => {
                const rtToggle = document.getElementById('realtime-toggle');
                if (rtToggle && rtToggle.checked) {
                    await fetchStats(false);
                    if (roomSelect.value) {
                        await loadMessages(true);
                    }
                }
            }, 3000);
        }
    }

    let mockRooms = ['mock_room_alpha', 'mock_room_beta', 'mock_room_gamma'];
    let mockTotalMsgs = 15204;
    let isMockMode = false;

    async function fetchRooms() {
        try {
            const res = await fetch(`${API_BASE}/rooms`);
            if(!res.ok) throw new Error("API Offline");
            const data = await res.json();
            
            roomSelect.innerHTML = '<option value="" disabled selected>Select a Room ID...</option>';
            if (data.rooms && data.rooms.length > 0) {
                const sortedRooms = data.rooms.sort((a, b) => (parseInt(a.replace(/\D/g, '')) || 0) - (parseInt(b.replace(/\D/g, '')) || 0));
                sortedRooms.forEach(room => {
                    const option = document.createElement('option');
                    option.value = room; option.textContent = room;
                    roomSelect.appendChild(option);
                });
            } else {
                roomSelect.innerHTML = '<option value="" disabled>No rooms available</option>';
            }
            isMockMode = false;
        } catch (error) {
            console.warn('Backend disconnected. Entering Pipeline Mock Mode.');
            isMockMode = true;
            roomSelect.innerHTML = '<option value="" disabled selected>Select a Room ID...</option>';
            mockRooms.forEach(room => {
                const option = document.createElement('option');
                option.value = room; option.textContent = room + " (Live Stream)";
                roomSelect.appendChild(option);
            });
        }
    }

    async function fetchStats(animate = true) {
        try {
            const healthRes = await fetch(`${API_BASE}/health`);
            if(!healthRes.ok) throw new Error("API Offline");
            const healthData = await healthRes.json();
            
            if (healthData.status === 'healthy') {
                statusBadge.classList.add('healthy'); statusBadge.classList.remove('error');
                statusText.innerText = 'Backend: Connected (Live)';
            } else throw new Error('Unhealthy');

            const statsRes = await fetch(`${API_BASE}/stats`);
            const statsData = await statsRes.json();
            
            document.querySelectorAll('.tooltip').forEach(t => t.style.display = 'none');
            
            if (animate) {
                animateValue(roomsVal, 0, statsData.total_rooms || 0, 1000);
                animateValue(msgsVal, 0, statsData.total_messages || 0, 1500);
            } else {
                roomsVal.innerHTML = (statsData.total_rooms || 0).toLocaleString();
                msgsVal.innerHTML = (statsData.total_messages || 0).toLocaleString();
            }
        } catch (error) {
            statusBadge.classList.add('error'); statusBadge.classList.remove('healthy');
            statusText.innerText = 'Mode: Standalone / Mock';
            
            // In Mock mode, we simulate live incoming data
            mockTotalMsgs += Math.floor(Math.random() * 5); 
            
            if (animate) {
                animateValue(roomsVal, 0, mockRooms.length, 1000);
                animateValue(msgsVal, 0, mockTotalMsgs, 1500);
            } else {
                roomsVal.innerHTML = mockRooms.length.toLocaleString();
                msgsVal.innerHTML = mockTotalMsgs.toLocaleString();
            }
            document.querySelectorAll('.tooltip').forEach(t => t.style.display = 'none'); // Disable tooltips so it looks intentional
        }
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    const loadMoreBtn = document.getElementById('load-more-btn');
    let currentPagingState = null;
    let mockPageCounter = 0;

    async function loadMessages(isBackground = false, isLoadMore = false) {
        const roomId = roomSelect.value;
        if (!roomId) return;

        if (!isBackground) {
            if (isLoadMore) { loadMoreBtn.innerText = 'Loading...'; loadMoreBtn.disabled = true; } 
            else { loadBtn.innerText = 'Loading...'; loadBtn.disabled = true; chatContainer.style.opacity = '0.5'; currentPagingState = null; mockPageCounter = 0; }
        }

        if (isMockMode) {
            setTimeout(() => {
                const isScrolled = chatContainer.scrollTop > 50;
                if (!isLoadMore) chatContainer.innerHTML = '';
                chatContainer.style.opacity = '1';

                const numMessages = isBackground ? Math.floor(Math.random() * 2) : 20; // Only push 0-1 msgs on background poll
                
                if (numMessages > 0) {
                    for(let i=0; i<numMessages; i++) {
                        const msgDiv = document.createElement('div');
                        msgDiv.className = 'message';
                        if (!isBackground) {
                            msgDiv.style.opacity = '0';
                            msgDiv.style.animation = `fadeIn 0.3s ease forwards ${i * 0.02}s`;
                        }
                        const users = ['user_4815', 'admin_99', 'guest_102', 'data_bot'];
                        const msgs = ['Checking the pipeline throughput.', 'Everything looks stable right now.', 'Can we analyze the recent spike?', 'ScyllaDB connection dropped temporarily.', 'Re-syncing nodes...'];
                        
                        msgDiv.innerHTML = `<div class="message-header"><span class="message-user">${users[Math.floor(Math.random()*users.length)]}</span><span>${formatDate(new Date().toISOString())}</span></div><div class="message-content">${msgs[Math.floor(Math.random()*msgs.length)]}</div>`;
                        
                        if(isBackground) chatContainer.prepend(msgDiv); // prepend live messages
                        else chatContainer.appendChild(msgDiv);
                    }
                }
                
                if (!isBackground && !isLoadMore && !isScrolled) chatContainer.scrollTop = 0;

                if (!isBackground) {
                    mockPageCounter++;
                    if (mockPageCounter < 3) { loadMoreBtn.style.display = 'inline-block'; } 
                    else { loadMoreBtn.style.display = 'none'; }
                    
                    loadBtn.innerText = 'Explore Messages'; loadBtn.disabled = false;
                    if(loadMoreBtn) { loadMoreBtn.innerText = 'Load More Messages'; loadMoreBtn.disabled = false; }
                }
            }, isBackground ? 0 : 500);
            return;
        }

        let url = `${API_BASE}/messages?room_id=${roomId}&limit=50`;
        if (isLoadMore && currentPagingState) url += `&state=${encodeURIComponent(currentPagingState)}`;

        try {
            const res = await fetch(url);
            if(!res.ok) throw new Error("API Offline");
            const data = await res.json();
            const isScrolled = chatContainer.scrollTop > 50;

            if (!isLoadMore) chatContainer.innerHTML = ''; 
            chatContainer.style.opacity = '1';

            if (data.data && data.data.length > 0) {
                data.data.forEach((msg, index) => {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'message';
                    if (!isBackground) {
                        msgDiv.style.opacity = '0';
                        msgDiv.style.animation = `fadeIn 0.3s ease forwards ${index * 0.02}s`;
                    }
                    msgDiv.innerHTML = `<div class="message-header"><span class="message-user">${msg.user_id}</span><span>${formatDate(msg.timestamp)}</span></div><div class="message-content">${msg.content}</div>`;
                    chatContainer.appendChild(msgDiv);
                });
                
                if (!isBackground && !isLoadMore && !isScrolled) chatContainer.scrollTop = 0;
                
                currentPagingState = data.paging_state;
                if (currentPagingState && !isBackground) loadMoreBtn.style.display = 'inline-block';
                else loadMoreBtn.style.display = 'none';
            } else {
                if (!isLoadMore) chatContainer.innerHTML = `<div class="empty-state"><p>No messages found in this room.</p></div>`;
                loadMoreBtn.style.display = 'none';
            }
        } catch (error) {
            if (!isBackground) {
                chatContainer.style.opacity = '1';
                if (!isLoadMore) chatContainer.innerHTML = `<div class="empty-state" style="color: #FF3B30;"><p>API Connection Failed.</p></div>`;
            }
        } finally {
            if (!isBackground) {
                loadBtn.innerText = 'Explore Messages'; loadBtn.disabled = false;
                if(loadMoreBtn) { loadMoreBtn.innerText = 'Load More Messages'; loadMoreBtn.disabled = false; }
            }
        }
    }

    if (loadBtn) loadBtn.addEventListener('click', () => loadMessages(false, false));
    if (loadMoreBtn) loadMoreBtn.addEventListener('click', () => loadMessages(false, true));
    if (roomSelect) roomSelect.addEventListener('change', () => {
        if (roomSelect.value) { loadBtn.disabled = false; loadMessages(false, false); }
    });

    // --- Moving Average & Chart Logic for Pipeline Tab ---
    function renderMockSentimentTrend() {
        const ctx = document.getElementById('sentimentTrendChart');
        if(!ctx) return;
        
        // Generate high-frequency noise data (e.g. 30 days)
        const days = Array.from({length: 30}, (_, i) => `Day ${i+1}`);
        const rawData = Array.from({length: 30}, () => Math.random() * 100);
        
        // Apply Moving Average Smoothing (window = 5)
        const windowSize = 5;
        const smoothedData = rawData.map((val, idx, arr) => {
            const start = Math.max(0, idx - windowSize + 1);
            const subset = arr.slice(start, idx + 1);
            return subset.reduce((sum, v) => sum + v, 0) / subset.length;
        });

        if (sentimentTrendChartInstance) sentimentTrendChartInstance.destroy();
        sentimentTrendChartInstance = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: days,
                datasets: [
                    { label: 'Raw Noise', data: rawData, borderColor: 'rgba(56, 189, 248, 0.2)', borderWidth: 1, borderDash: [5,5], pointRadius: 0, tension: 0.3 },
                    { label: 'Moving Average (5-Day)', data: smoothedData, borderColor: '#0ea5e9', borderWidth: 3, pointBackgroundColor: '#0f172a', pointBorderColor: '#0ea5e9', tension: 0.4 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, color: '#94a3b8', scales: { x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } }, y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } } }, plugins: { legend: { labels: { color: '#cbd5e1' } } } }
        });
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

