document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const messagesList = document.getElementById('messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    // 1. On connection, join the room
    socket.on('connect', () => {
        console.log('Connected to server.');
        socket.emit('join', { room_id: ROOM_ID });
    });

    // 2. Listen for new messages
    socket.on('new_message', (data) => {
        addMessage(data, false);
    });

    // 3. Listen for status messages (e.g., user join)
    socket.on('status', (data) => {
        addMessage(data, true);
    });

    // 4. Handle send button click
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const text = messageInput.value.trim();
        if (text) {
            socket.emit('send_message', {
                room_id: ROOM_ID,
                text: text
            });
            messageInput.value = '';
        }
    }

    function addMessage(data, isStatus = false) {
        const li = document.createElement('li');
        if (isStatus) {
            li.className = 'status-msg';
            li.textContent = data.msg;
        } else {
            li.className = 'user-msg';
            const authorSpan = document.createElement('span');
            authorSpan.className = 'author';
            authorSpan.textContent = `${data.user.nickname || data.user.username}: `;
            
            const textSpan = document.createElement('span');
            textSpan.className = 'text';
            textSpan.textContent = data.text;

            li.appendChild(authorSpan);
            li.appendChild(textSpan);
        }
        messagesList.appendChild(li);
        messagesList.scrollTop = messagesList.scrollHeight; // Scroll to bottom
    }
});
