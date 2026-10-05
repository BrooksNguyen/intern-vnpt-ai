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
    let isPolling = false;
    
    // Add real-time toggle UI
    const searchControls = document.querySelector('.search-controls');
    if (searchControls) {
        const toggleHtml = `
            <label style="display:flex; align-items:center; gap:0.5rem; font-size:0.9rem; color:#666; cursor:pointer; margin-left:1rem;">
                <input type="checkbox" id="realtime-toggle" checked style="accent-color:#005baa; width:16px; height:16px;">
                Live Sync
            </label>
        `;
        searchControls.insertAdjacentHTML('beforeend', toggleHtml);
    }

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
        
        // Setup Real-Time Polling
        if (!pollInterval) {
            pollInterval = setInterval(async () => {
                const rtToggle = document.getElementById('realtime-toggle');
                if (rtToggle && rtToggle.checked) {
                    await fetchStats(false); // background fetch
                    if (roomSelect.value) {
                        await loadMessages(true); // background fetch
                    }
                }
            }, 3000);
        }
    }

    async function fetchRooms() {
        try {
            const res = await fetch(`${API_BASE}/rooms`);
            const data = await res.json();
            
            roomSelect.innerHTML = '<option value="" disabled selected>Select a Room ID...</option>';
            if (data.rooms && data.rooms.length > 0) {
                const sortedRooms = data.rooms.sort((a, b) => {
                    const numA = parseInt(a.replace(/\D/g, '')) || 0;
                    const numB = parseInt(b.replace(/\D/g, '')) || 0;
                    return numA - numB;
                });
                
                sortedRooms.forEach(room => {
                    const option = document.createElement('option');
                    option.value = room;
                    option.textContent = room;
                    roomSelect.appendChild(option);
                });
            } else {
                roomSelect.innerHTML = '<option value="" disabled>No rooms available</option>';
            }
        } catch (error) {
            console.error('Error fetching rooms:', error);
            roomSelect.innerHTML = '<option value="" disabled>Failed to load rooms</option>';
        }
    }

    async function fetchStats(animate = true) {
        try {
            const healthRes = await fetch(`${API_BASE}/health`);
            const healthData = await healthRes.json();
            
            if (healthData.status === 'healthy') {
                statusBadge.classList.add('healthy');
                statusBadge.classList.remove('error');
                statusText.innerText = 'API Connected (Live)';
            } else throw new Error('Unhealthy');

            const statsRes = await fetch(`${API_BASE}/stats`);
            const statsData = await statsRes.json();
            
            if (animate) {
                animateValue(roomsVal, 0, statsData.total_rooms || 0, 1000);
                animateValue(msgsVal, 0, statsData.total_messages || 0, 1500);
            } else {
                roomsVal.innerHTML = (statsData.total_rooms || 0).toLocaleString();
                msgsVal.innerHTML = (statsData.total_messages || 0).toLocaleString();
            }

        } catch (error) {
            statusBadge.classList.add('error');
            statusBadge.classList.remove('healthy');
            statusText.innerText = 'API Offline';
            roomsVal.innerText = 'N/A'; msgsVal.innerText = 'N/A';
        }
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', { 
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
    }

    const loadMoreBtn = document.getElementById('load-more-btn');
    let currentPagingState = null;

    async function loadMessages(isBackground = false, isLoadMore = false) {
        const roomId = roomSelect.value;
        if (!roomId) return;

        if (!isBackground) {
            if (isLoadMore) {
                loadMoreBtn.innerText = 'Loading...';
                loadMoreBtn.disabled = true;
            } else {
                loadBtn.innerText = 'Loading...';
                loadBtn.disabled = true;
                chatContainer.style.opacity = '0.5';
                currentPagingState = null;
            }
        }

        let url = `${API_BASE}/messages?room_id=${roomId}&limit=50`;
        if (isLoadMore && currentPagingState) {
            url += `&state=${encodeURIComponent(currentPagingState)}`;
        }

        try {
            const res = await fetch(url);
            const data = await res.json();
            
            // Check if user has scrolled up
            const isScrolled = chatContainer.scrollTop > 50;

            if (!isLoadMore) {
                chatContainer.innerHTML = ''; 
            }
            chatContainer.style.opacity = '1';

            if (data.data && data.data.length > 0) {
                data.data.forEach((msg, index) => {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'message';
                    
                    if (!isBackground) {
                        msgDiv.style.opacity = '0';
                        msgDiv.style.animation = `fade-in 0.3s ease forwards ${index * 0.02}s`;
                    }
                    
                    msgDiv.innerHTML = `
                        <div class="message-header">
                            <span class="message-user">${msg.user_id}</span>
                            <span>${formatDate(msg.timestamp)}</span>
                        </div>
                        <div class="message-content">${msg.content}</div>
                    `;
                    chatContainer.appendChild(msgDiv);
                });
                
                if (!isBackground && !isLoadMore && !isScrolled) {
                    chatContainer.scrollTop = 0;
                }
                
                currentPagingState = data.paging_state;
                if (currentPagingState && !isBackground) {
                    loadMoreBtn.style.display = 'inline-block';
                } else {
                    loadMoreBtn.style.display = 'none';
                }

            } else {
                if (!isLoadMore) {
                    chatContainer.innerHTML = `<div class="empty-state"><p>No messages found in this room.</p></div>`;
                }
                loadMoreBtn.style.display = 'none';
            }

        } catch (error) {
            if (!isBackground) {
                chatContainer.style.opacity = '1';
                if (!isLoadMore) {
                    chatContainer.innerHTML = `<div class="empty-state" style="color: #FF3B30;"><p>API Connection Failed.</p></div>`;
                }
            }
        } finally {
            if (!isBackground) {
                loadBtn.innerText = 'Explore Messages';
                loadBtn.disabled = false;
                loadMoreBtn.innerText = 'Load More Messages';
                loadMoreBtn.disabled = false;
            }
        }
    }

    loadBtn.addEventListener('click', () => loadMessages(false, false));
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => loadMessages(false, true));
    }
    roomSelect.addEventListener('change', () => {
        if (roomSelect.value) {
            loadBtn.disabled = false;
            loadMessages(false, false); // Auto-load on select change
        }
    });
    
    // --- Kaggle Analyzer Logic ---
    const kaggleBtn = document.getElementById('kaggle-btn');
    const kaggleSlug = document.getElementById('kaggle-slug');
    const kaggleColumn = document.getElementById('kaggle-column');
    const kaggleContainer = document.getElementById('kaggle-results-container');

    kaggleBtn.addEventListener('click', async () => {
        let slug = kaggleSlug.value.trim();
        if (!slug) {
            alert('Please enter a valid Kaggle Dataset Slug (e.g., kazanova/sentiment140)');
            return;
        }

        // Automatically extract slug if user pastes a full URL
        try {
            if (slug.includes('kaggle.com/datasets/')) {
                const urlObj = new URL(slug);
                const pathParts = urlObj.pathname.split('/').filter(Boolean);
                if (pathParts.length >= 3 && pathParts[0] === 'datasets') {
                    slug = `${pathParts[1]}/${pathParts[2]}`;
                }
            } else if (slug.startsWith('https://') || slug.startsWith('http://')) {
                alert('Please provide a valid Kaggle dataset URL or just the slug.');
                return;
            }
        } catch (e) {
            // Ignore URL parse errors and fall back to whatever they entered
        }

        kaggleBtn.innerText = 'Analyzing...';
        kaggleBtn.disabled = true;
        kaggleContainer.innerHTML = `<div class="empty-state"><p>Downloading and analyzing dataset via Kaggle API. This may take a minute depending on the dataset size...</p></div>`;
        kaggleContainer.style.opacity = '0.7';

        let url = `${API_BASE}/analyze/kaggle?dataset=${encodeURIComponent(slug)}`;
        if (kaggleColumn.value.trim()) {
            url += `&text_column=${encodeURIComponent(kaggleColumn.value.trim())}`;
        }

        try {
            const res = await fetch(url);
            const text = await res.text();
            
            let data;
            try {
                data = JSON.parse(text);
            } catch (err) {
                throw new Error(res.ok ? "Invalid JSON from server" : `Server Error: ${res.status}. ${text.slice(0, 100)}`);
            }

            if (!res.ok) {
                throw new Error(data.detail || 'Analysis failed');
            }

            kaggleContainer.style.opacity = '1';
            
            // Check if mock data
            const isMock = data.csv_analyzed === "mock_data.csv";
            const warningHtml = isMock ? `
                <div style="background: rgba(255, 59, 48, 0.1); border: 1px solid #FF3B30; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; display: flex; gap: 1rem; align-items: flex-start;">
                    <svg viewBox="0 0 24 24" width="24" height="24" stroke="#FF3B30" stroke-width="2" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                    <div>
                        <strong style="color: #FF3B30; display: block; margin-bottom: 0.25rem;">Mock Data Triggered (Kaggle Auth Missing)</strong>
                        <p style="color: #666; font-size: 0.9rem; margin: 0;">To analyze real datasets, you must provide your <code style="background:#eee;padding:2px 4px;border-radius:4px;">KAGGLE_USERNAME</code> and <code style="background:#eee;padding:2px 4px;border-radius:4px;">KAGGLE_KEY</code> as Environment Variables in your Render Dashboard.</p>
                    </div>
                </div>
            ` : '';

            // Build Results UI
            kaggleContainer.innerHTML = `
                <div style="animation: fade-in 0.4s ease forwards; width:100%">
                    <h3 style="color:var(--vnpt-blue-dark); margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:center;">
                        Dataset: ${data.dataset}
                        <span style="font-size:0.8rem; background:rgba(0,180,216,0.1); color:var(--vnpt-blue-main); padding:4px 12px; border-radius:20px;">Analysis Complete</span>
                    </h3>
                    
                    ${warningHtml}
                    
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:2rem;">
                        <div style="background:var(--bg-surface); padding:1.5rem; border-radius:var(--radius-sm); border:1px solid var(--border-color); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                            <div style="color:var(--text-muted); font-size:0.85rem; text-transform:uppercase; font-weight:600; margin-bottom:0.5rem">CSV File Analyzed</div>
                            <div style="font-size:1.1rem; font-weight:600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${data.csv_analyzed}</div>
                        </div>
                        <div style="background:var(--bg-surface); padding:1.5rem; border-radius:var(--radius-sm); border:1px solid var(--border-color); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                            <div style="color:var(--text-muted); font-size:0.85rem; text-transform:uppercase; font-weight:600; margin-bottom:0.5rem">Target Column</div>
                            <div style="font-size:1.1rem; font-weight:600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${data.column_analyzed}</div>
                        </div>
                    </div>
                    
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;">
                        <div style="background:var(--bg-surface); padding:1.5rem; border-radius:var(--radius-sm); border:1px solid var(--border-color); display:flex; flex-direction:column; align-items:center;">
                            <div style="color:var(--text-muted); font-size:0.85rem; text-transform:uppercase; font-weight:600; margin-bottom:1rem; align-self:flex-start;">Sentiment Distribution</div>
                            <div style="position: relative; width: 100%; max-width: 250px; aspect-ratio: 1;">
                                <canvas id="sentimentChart"></canvas>
                            </div>
                        </div>
                        <div style="background:var(--bg-surface); padding:1.5rem; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
                            <div style="color:var(--text-muted); font-size:0.85rem; text-transform:uppercase; font-weight:600; margin-bottom:1rem;">Top Extracted Keywords</div>
                            <div style="position: relative; width: 100%; height: 250px;">
                                <canvas id="keywordsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Render Charts after DOM updates
            setTimeout(() => {
                const ctxSentiment = document.getElementById('sentimentChart').getContext('2d');
                new Chart(ctxSentiment, {
                    type: 'doughnut',
                    data: {
                        labels: ['Positive', 'Negative', 'Neutral'],
                        datasets: [{
                            data: [data.sentiment_distribution.positive, data.sentiment_distribution.negative, data.sentiment_distribution.neutral],
                            backgroundColor: ['#34C759', '#FF3B30', '#8E8E93'],
                            borderWidth: 0
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
                });

                const ctxKeywords = document.getElementById('keywordsChart').getContext('2d');
                const labels = data.top_keywords.map(k => k.word);
                const counts = data.top_keywords.map(k => k.count);
                new Chart(ctxKeywords, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Word Frequency',
                            data: counts,
                            backgroundColor: 'rgba(0, 91, 170, 0.8)',
                            borderRadius: 4
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
                });
            }, 50);

        } catch (error) {
            kaggleContainer.style.opacity = '1';
            kaggleContainer.innerHTML = `<div class="empty-state" style="color: #FF3B30;"><p>Error: ${error.message}</p></div>`;
        } finally {
            kaggleBtn.innerText = 'Analyze Dataset';
            kaggleBtn.disabled = false;
        }
    });

    
    // Add simple fade-in keyframe dynamically for messages
    const style = document.createElement('style');
    style.innerHTML = `@keyframes fade-in { to { opacity: 1; transform: translateY(0); } }`;
    document.head.appendChild(style);
});
