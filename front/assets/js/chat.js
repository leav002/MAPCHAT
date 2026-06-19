document.addEventListener('DOMContentLoaded', () => {
    console.log("Chat JS Loaded. Room:", ROOM_ID, "User:", USER_ID);
    const socket = io();

    const messagesList = document.getElementById('messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const imageUpload = document.getElementById('image-upload');
    const errorDisplay = document.getElementById('error-display');

    let currentCoords = null;

    if ('geolocation' in navigator) {
        navigator.geolocation.watchPosition((pos) => {
            currentCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        }, (err) => console.warn("GPS Error:", err));
    }

    socket.on('connect', () => {
        console.log("Socket Connected to Server");
        socket.emit('join', { room_id: ROOM_ID, user_id: USER_ID });
    });

    socket.on('new_message', (data) => {
        console.log("Received Message:", data);
        addMessage(data, false);
    });

    socket.on('status', (data) => {
        console.log("Status Update:", data);
        addMessage(data, true);
    });

    socket.on('error', (data) => {
        console.error("Socket Error:", data);
        errorDisplay.textContent = data.msg;
        errorDisplay.style.display = 'block';
        setTimeout(() => { errorDisplay.style.display = 'none'; }, 3000);
    });

    function sendMessage(imgData = null) {
        const text = messageInput.value.trim();
        if (text || imgData) {
            console.log("Sending Message...", { text, hasImage: !!imgData });
            socket.emit('send_message', {
                room_id: ROOM_ID,
                user_id: USER_ID,
                text: text,
                image: imgData,
                lat: currentCoords ? currentCoords.lat : null,
                lng: currentCoords ? currentCoords.lng : null
            });
            messageInput.value = '';
        }
    }

    sendButton.addEventListener('click', () => sendMessage());
    messageInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

    imageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (evt) => sendMessage(evt.target.result);
            reader.readAsDataURL(file);
        }
    });

    function addMessage(data, isStatus = false) {
        const li = document.createElement('li');
        if (isStatus) {
            li.className = 'status-msg';
            li.textContent = data.msg;
        } else {
            const isMine = data.user.id === USER_ID;
            li.className = isMine ? 'mine' : 'others';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'msg-content';
            
            const nickname = document.createElement('div');
            nickname.style.fontSize = '0.7em';
            nickname.style.marginBottom = '2px';
            nickname.textContent = data.user.nickname || data.user.username;
            li.appendChild(nickname);

            if (data.text) {
                const p = document.createElement('p');
                p.textContent = data.text;
                p.style.margin = '0';
                contentDiv.appendChild(p);
            }
            if (data.image) {
                const img = document.createElement('img');
                img.src = data.image;
                img.className = 'chat-img';
                contentDiv.appendChild(img);
            }
            li.appendChild(contentDiv);
        }
        messagesList.appendChild(li);
        messagesList.scrollTop = messagesList.scrollHeight;
    }
});
