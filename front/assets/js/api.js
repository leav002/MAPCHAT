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
            // Try to parse error json, but fallback to status text if it fails
            let errorMessage = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                // Ignore if response is not json
            }
            throw new Error(errorMessage);
        }

        // If status is 204, creation was successful but there's no content to parse
        if (response.status === 204) {
            return null;
        }

        // For other success statuses (like 200 or 201), parse and return the json
        return await response.json();
    } catch (error) {
        console.error("Error creating chat room:", error);
        throw error;
    }
}
