document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = '/api';

    // DOM Elements
    const statusBadge = document.getElementById('api-status');
    const statusText = statusBadge.querySelector('.status-text');
    const roomsVal = document.getElementById('rooms-val');
    const msgsVal = document.getElementById('msgs-val');
    
    const roomInput = document.getElementById('room-input');
    const loadBtn = document.getElementById('load-btn');
    const chatContainer = document.getElementById('chat-container');

    // Smooth counter animation
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Fetch initial metrics with graceful error handling
    async function fetchStats() {
        try {
            const healthRes = await fetch(`${API_BASE}/health`);
            const healthData = await healthRes.json();
            
            if (healthData.status === 'healthy') {
                statusBadge.classList.add('healthy');
                statusBadge.classList.remove('error');
                statusText.innerText = 'Connected to ScyllaDB';
            } else {
                throw new Error('Unhealthy');
            }

            const statsRes = await fetch(`${API_BASE}/stats`);
            const statsData = await statsRes.json();
            
            const totalRooms = statsData.total_rooms || 0;
            const totalMsgs = statsData.total_messages || 0;

            animateValue(roomsVal, 0, totalRooms, 1000);
            animateValue(msgsVal, 0, totalMsgs, 1500);

        } catch (error) {
            console.error('API Error:', error);
            statusBadge.classList.add('error');
            statusBadge.classList.remove('healthy');
            statusText.innerText = 'Offline';
            roomsVal.innerText = 'N/A';
            msgsVal.innerText = 'N/A';
        }
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const d = new Date(dateString);
        return d.toLocaleDateString('en-US', { 
            month: 'short', day: 'numeric', 
            hour: '2-digit', minute: '2-digit' 
        });
    }

    function getDeviceEmoji(device) {
        const map = { 'ios': '📱', 'android': '🤖', 'web': '🌐', 'desktop': '💻' };
        return map[device] || '💬';
    }

    // Fetch and render messages
    async function loadMessages() {
        const roomId = roomInput.value.trim();
        if (!roomId) return;

        // UI Loading state
        loadBtn.innerText = 'Loading';
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
                    msgDiv.style.animationDelay = `${index * 0.04}s`; // Staggered fade in
                    
                    msgDiv.innerHTML = `
                        <div class="message-header">
                            <span class="message-user">${msg.user_id} ${getDeviceEmoji(msg.device)}</span>
                            <span>${formatDate(msg.timestamp)}</span>
                        </div>
                        <div class="message-content">
                            ${msg.content}
                        </div>
                    `;
                    chatContainer.appendChild(msgDiv);
                });
                
                // Smooth scroll to top of chat
                chatContainer.scrollTop = 0;
            } else {
                chatContainer.innerHTML = `
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><path d="M10 9l5 3-5 3V9z"></path></svg>
                        <p>No messages found in ${roomId}</p>
                    </div>`;
            }

        } catch (error) {
            console.error('Error fetching messages:', error);
            chatContainer.style.opacity = '1';
            chatContainer.innerHTML = `
                <div class="empty-state" style="color: #FF3B30;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <p>Failed to connect to the API</p>
                </div>`;
        } finally {
            loadBtn.innerText = 'Explore';
            loadBtn.disabled = false;
        }
    }

    // Event Listeners
    loadBtn.addEventListener('click', loadMessages);
    roomInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadMessages();
            // Blur input to dismiss keyboard on mobile (iOS friendly)
            roomInput.blur();
        }
    });

    // Boot up
    fetchStats();
});
