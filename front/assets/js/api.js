async function fetchNearbyChatRooms(lat, lng) {
    try {
        const response = await fetch(`/api/chat-rooms?lat=${lat}&lng=${lng}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching nearby chat rooms:", error);
        return [];
    }
}

async function createChatRoom(name, lat, lng) {
    try {
        const response = await fetch('/api/chat-rooms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, lat, lng }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error creating chat room:", error);
        throw error;
    }
}
