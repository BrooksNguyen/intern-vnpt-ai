document.addEventListener('DOMContentLoaded', () => {
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

    // Week 12 Requirement: Fetch Rooms to populate Selectbox
    async function fetchRooms() {
        try {
            const res = await fetch(`${API_BASE}/rooms`);
            const data = await res.json();
            
            roomSelect.innerHTML = '<option value="" disabled selected>Select a Room ID...</option>';
            if (data.rooms && data.rooms.length > 0) {
                // Sort rooms alphabetically for better UX
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
                loadBtn.disabled = false;
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
                statusText.innerText = 'Connected to API';
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

    function getDeviceEmoji(device) {
        const map = { 'ios': '📱', 'android': '🤖', 'web': '🌐', 'desktop': '💻' };
        return map[device] || '💬';
    }

    async function loadMessages() {
        const roomId = roomSelect.value;
        if (!roomId) return;

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
                    msgDiv.style.animationDelay = `${index * 0.03}s`;
                    
                    msgDiv.innerHTML = `
                        <div class="message-header">
                            <span class="message-user">${msg.user_id} ${getDeviceEmoji(msg.device)}</span>
                            <span>${formatDate(msg.timestamp)}</span>
                        </div>
                        <div class="message-content">${msg.content}</div>
                    `;
                    chatContainer.appendChild(msgDiv);
                });
                chatContainer.scrollTop = 0;
            } else {
                chatContainer.innerHTML = `<div class="empty-state"><p>No messages found.</p></div>`;
            }

        } catch (error) {
            chatContainer.style.opacity = '1';
            chatContainer.innerHTML = `<div class="empty-state" style="color: #FF3B30;"><p>API Connection Failed</p></div>`;
        } finally {
            loadBtn.innerText = 'Explore';
            loadBtn.disabled = false;
        }
    }

    loadBtn.addEventListener('click', loadMessages);
    roomSelect.addEventListener('change', () => {
        if (roomSelect.value) {
            loadBtn.disabled = false;
        }
    });

    fetchStats();
    fetchRooms();
});
