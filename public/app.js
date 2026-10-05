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
        fetchStats();
        fetchRooms();
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

    async function fetchStats() {
        try {
            const healthRes = await fetch(`${API_BASE}/health`);
            const healthData = await healthRes.json();
            
            if (healthData.status === 'healthy') {
                statusBadge.classList.add('healthy');
                statusBadge.classList.remove('error');
                statusText.innerText = 'API Connected';
            } else throw new Error('Unhealthy');

            const statsRes = await fetch(`${API_BASE}/stats`);
            const statsData = await statsRes.json();
            
            animateValue(roomsVal, 0, statsData.total_rooms || 0, 1000);
            animateValue(msgsVal, 0, statsData.total_messages || 0, 1500);

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
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
        });
    }

    async function loadMessages() {
        const roomId = roomSelect.value;
        if (!roomId) return;

        loadBtn.innerText = 'Loading...';
        loadBtn.disabled = true;
        chatContainer.style.opacity = '0.5';

        try {
            const res = await fetch(`${API_BASE}/messages?room_id=${roomId}&limit=50`);
            const data = await res.json();

            chatContainer.innerHTML = ''; 
            chatContainer.style.opacity = '1';

            if (data.data && data.data.length > 0) {
                data.data.forEach((msg, index) => {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'message';
                    
                    // Small fade-in animation
                    msgDiv.style.opacity = '0';
                    msgDiv.style.animation = `fade-in 0.4s ease forwards ${index * 0.03}s`;
                    
                    msgDiv.innerHTML = `
                        <div class="message-header">
                            <span class="message-user">${msg.user_id}</span>
                            <span>${formatDate(msg.timestamp)}</span>
                        </div>
                        <div class="message-content">${msg.content}</div>
                    `;
                    chatContainer.appendChild(msgDiv);
                });
                chatContainer.scrollTop = 0;
            } else {
                chatContainer.innerHTML = `<div class="empty-state"><p>No messages found in this room.</p></div>`;
            }

        } catch (error) {
            chatContainer.style.opacity = '1';
            chatContainer.innerHTML = `<div class="empty-state" style="color: #FF3B30;"><p>API Connection Failed. Please ensure the backend is running.</p></div>`;
        } finally {
            loadBtn.innerText = 'Explore Messages';
            loadBtn.disabled = false;
        }
    }

    loadBtn.addEventListener('click', loadMessages);
    roomSelect.addEventListener('change', () => {
        if (roomSelect.value) {
            loadBtn.disabled = false;
        }
    });
    
    // Add simple fade-in keyframe dynamically for messages
    const style = document.createElement('style');
    style.innerHTML = `@keyframes fade-in { to { opacity: 1; transform: translateY(0); } }`;
    document.head.appendChild(style);
});
