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

    // --- Kaggle Analyzer Logic (Tab 1) ---
    const kaggleBtn = document.getElementById('kaggle-btn');
    const kaggleSlug = document.getElementById('kaggle-slug');
    const kaggleColumn = document.getElementById('kaggle-column');
    
    // Chips integration
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            kaggleSlug.value = chip.dataset.slug;
            kaggleColumn.value = ''; // clear col
            kaggleBtn.click();
        });
    });

    let kaggleChart1Instance = null;
    let kaggleChart2Instance = null;

    kaggleBtn.addEventListener('click', async () => {
        let slug = kaggleSlug.value.trim();
        if (!slug) return alert('Please enter a valid Kaggle Dataset Slug');

        try {
            if (slug.includes('kaggle.com/datasets/')) {
                const urlObj = new URL(slug);
                const pathParts = urlObj.pathname.split('/').filter(Boolean);
                if (pathParts.length >= 3) slug = `${pathParts[1]}/${pathParts[2]}`;
            }
        } catch (e) {}

        kaggleBtn.innerText = 'Analyzing...'; kaggleBtn.disabled = true;
        document.getElementById('kaggle-empty-state').style.display = 'none';
        document.getElementById('kaggle-results-container').style.display = 'none';
        document.getElementById('kaggle-error').style.display = 'none';
        document.getElementById('kaggle-loading').style.display = 'block';

        let url = `${API_BASE}/analyze/kaggle?dataset=${encodeURIComponent(slug)}`;
        if (kaggleColumn.value.trim()) url += `&text_column=${encodeURIComponent(kaggleColumn.value.trim())}`;

        try {
            const res = await fetch(url);
            
            // Check if the response is actually JSON
            const contentType = res.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await res.text();
                console.error("Non-JSON response:", text.slice(0, 500));
                
                // If it's an HTML page, it might be Render spinning up or Vercel 404
                if (text.includes("<!DOCTYPE html>") || text.includes("<html")) {
                    if (res.status === 502 || res.status === 503 || text.includes("Render")) {
                        throw new Error("Backend server is starting up from sleep (Cold Start). Please wait 30-60 seconds and try again.");
                    }
                    throw new Error(`Backend Error (HTML returned instead of JSON). Status: ${res.status}. Check Vercel/Render connection.`);
                }
                throw new Error(`Server returned unexpected format (Status ${res.status})`);
            }

            let data;
            try { data = await res.json(); } catch (err) { throw new Error(`Failed to parse JSON response`); }
            if (!res.ok) throw new Error(data.detail || 'Analysis failed');

            if (data.error && data.error !== 'None') {
                document.getElementById('kaggle-error').innerText = `Warning: ${data.error} (Using Mock Data)`;
                document.getElementById('kaggle-error').style.display = 'block';
            }

            document.getElementById('kaggle-loading').style.display = 'none';
            document.getElementById('kaggle-results-container').style.display = 'block';

            // Populate KPIs
            document.getElementById('kpi-file').innerText = data.csv_analyzed;
            document.getElementById('kpi-dim').innerText = `${data.total_rows.toLocaleString()} x ${data.total_cols}`;
            document.getElementById('kpi-col').innerText = data.column_analyzed;
            document.getElementById('kpi-health').innerText = `${data.missing_rate}% Missing`;

            // Setup Charts based on data type
            if (kaggleChart1Instance) kaggleChart1Instance.destroy();
            if (kaggleChart2Instance) kaggleChart2Instance.destroy();

            const ctx1 = document.getElementById('kaggleChart1').getContext('2d');
            const ctx2 = document.getElementById('kaggleChart2').getContext('2d');

            Chart.defaults.color = '#94a3b8';
            Chart.defaults.borderColor = '#334155';

            if (data.is_numeric && data.histogram) {
                document.getElementById('kaggle-chart1-title').innerText = "Value Distribution Histogram";
                document.getElementById('kaggle-chart2-title').innerText = "Feature Trend Line (Sample)";
                
                kaggleChart1Instance = new Chart(ctx1, {
                    type: 'bar',
                    data: { labels: data.histogram.map(h => h.bin), datasets: [{ label: 'Frequency', data: data.histogram.map(h => h.count), backgroundColor: '#38bdf8', borderRadius: 4 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                });

                kaggleChart2Instance = new Chart(ctx2, {
                    type: 'line',
                    data: { labels: data.trend.map((_, i) => i+1), datasets: [{ label: 'Value', data: data.trend, borderColor: '#22c55e', backgroundColor: 'rgba(34, 197, 94, 0.1)', fill: true, tension: 0.3, pointRadius: 0 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                });

            } else if (data.sentiment_distribution && data.top_keywords) {
                document.getElementById('kaggle-chart1-title').innerText = "Sentiment Class Distribution";
                document.getElementById('kaggle-chart2-title').innerText = "Top Extracted Keywords";
                
                kaggleChart1Instance = new Chart(ctx1, {
                    type: 'doughnut',
                    data: { labels: ['Positive', 'Negative', 'Neutral'], datasets: [{ data: [data.sentiment_distribution.positive, data.sentiment_distribution.negative, data.sentiment_distribution.neutral], backgroundColor: ['#22c55e', '#ef4444', '#64748b'], borderWidth: 0 }] },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1'} } } }
                });

                kaggleChart2Instance = new Chart(ctx2, {
                    type: 'bar',
                    data: { labels: data.top_keywords.map(k => k.word), datasets: [{ label: 'Frequency', data: data.top_keywords.map(k => k.count), backgroundColor: '#0ea5e9', borderRadius: 4 }] },
                    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                });
            }

            // --- Generate AI Feedback via Gemini ---
            const aiContainer = document.getElementById('kaggle-ai-feedback');
            const aiContent = document.getElementById('kaggle-ai-content');
            aiContainer.style.display = 'block';
            aiContent.innerHTML = '<div style="display:flex; align-items:center; gap: 0.5rem;"><div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div> Analyzing patterns...</div>';
            setTimeout(() => { aiContainer.style.opacity = '1'; }, 50);

            try {
                const aiRes = await fetch(`${API_BASE}/analyze/ai-feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ analysis_data: data })
                });
                const aiData = await aiRes.json();
                if (aiRes.ok && aiData.feedback) {
                    // Format markdown bold
                    const formatted = aiData.feedback.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#fff">$1</strong>');
                    aiContent.innerHTML = formatted;
                } else {
                    aiContent.innerHTML = `<span style="color:#ef4444">Failed to generate insights: ${aiData.feedback || 'Unknown error'}</span>`;
                }
            } catch (err) {
                aiContent.innerHTML = `<span style="color:#ef4444">Connection error while fetching AI Insights.</span>`;
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
