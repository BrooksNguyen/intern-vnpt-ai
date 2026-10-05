document.addEventListener('DOMContentLoaded', () => {
    // API base path is relative since frontend and backend are on the same domain in Vercel
    const API_BASE = '/api';

    const statusVal = document.getElementById('status-val');
    const roomsVal = document.getElementById('rooms-val');
    const msgsVal = document.getElementById('msgs-val');
    
    const roomInput = document.getElementById('room-input');
    const loadBtn = document.getElementById('load-btn');
    const chatContainer = document.getElementById('chat-container');

    // Fetch initial stats
    async function fetchStats() {
        try {
            const healthRes = await fetch(`${API_BASE}/health`);
            const healthData = await healthRes.json();
            
            if (healthData.status === 'healthy') {
                statusVal.innerHTML = '🟢 Healthy';
                statusVal.style.color = '#4ade80';
            } else {
                statusVal.innerHTML = '🔴 DB Error';
                statusVal.style.color = '#f87171';
            }

            const statsRes = await fetch(`${API_BASE}/stats`);
            const statsData = await statsRes.json();
            
            roomsVal.innerText = statsData.total_rooms || 0;
            msgsVal.innerText = (statsData.total_messages || 0).toLocaleString();

        } catch (error) {
            console.error('Error fetching stats:', error);
            statusVal.innerHTML = '🟡 API Offline';
            statusVal.style.color = '#facc15';
        }
    }

    // Format date helper
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const d = new Date(dateString);
        return d.toLocaleString();
    }

    // Get device emoji
    function getDeviceEmoji(device) {
        const map = {
            'ios': '📱',
            'android': '🤖',
            'web': '🌐',
            'desktop': '💻'
        };
        return map[device] || '❓';
    }

    // Load messages
    async function loadMessages() {
        const roomId = roomInput.value.trim();
        if (!roomId) return;

        loadBtn.innerText = 'Loading...';
        loadBtn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/messages?room_id=${roomId}&limit=50`);
            const data = await res.json();

            chatContainer.innerHTML = ''; // Clear chat

            if (data.data && data.data.length > 0) {
                data.data.forEach((msg, index) => {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'message';
                    msgDiv.style.animationDelay = `${index * 0.05}s`;
                    
                    msgDiv.innerHTML = `
                        <div class="message-header">
                            <span class="message-user">${msg.user_id} ${getDeviceEmoji(msg.device)}</span>
                            <span>${msg.bucket_id} • ${formatDate(msg.timestamp)}</span>
                        </div>
                        <div class="message-content">
                            ${msg.content}
                        </div>
                    `;
                    chatContainer.appendChild(msgDiv);
                });
            } else {
                chatContainer.innerHTML = `<div class="empty-state">No messages found for ${roomId}.</div>`;
            }

        } catch (error) {
            console.error('Error fetching messages:', error);
            chatContainer.innerHTML = `<div class="empty-state" style="color: #f87171;">Failed to fetch messages. Check API connection.</div>`;
        } finally {
            loadBtn.innerText = 'Explore Messages ✨';
            loadBtn.disabled = false;
        }
    }

    // Event Listeners
    loadBtn.addEventListener('click', loadMessages);
    roomInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadMessages();
        }
    });

    // Initialize
    fetchStats();
});
