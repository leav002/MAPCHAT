document.addEventListener('DOMContentLoaded', () => {
    // Initialize the map and set its view to a default location
    const map = L.map('map').setView([37.5665, 126.9780], 13); // Default to Seoul

    // Add a tile layer to the map (e.g., OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Function to fetch and display chat rooms
    async function loadNearbyRooms(lat, lng) {
        const rooms = await fetchNearbyChatRooms(lat, lng);
        rooms.forEach(room => {
            L.marker([room.location.lat, room.location.lng])
                .addTo(map)
                .bindPopup(`<b>${room.name}</b><br><button onclick="joinChat(${room.id})">Join</button>`);
        });
    }

    // Get user's current location
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                map.setView([latitude, longitude], 15);
                L.marker([latitude, longitude], { icon: createCustomIcon() })
                    .addTo(map)
                    .bindPopup('Your current location').openPopup();
                
                // Load nearby rooms based on user's location
                loadNearbyRooms(latitude, longitude);
            },
            (error) => {
                console.error("Error getting user's location:", error);
                alert(
                    'Could not determine your location. \n\n' +
                    'Possible reasons:\n' +
                    '- You denied the location permission.\n' +
                    '- Your device\'s location service is turned off.\n' +
                    '- You are not on a secure connection (HTTPS).\n\n' +
                    'Showing default location (Seoul).'
                );
                // If location is denied, load rooms for the default location (Seoul)
                loadNearbyRooms(37.5665, 126.9780);
            }
        );
    } else {
        alert('Geolocation is not available in this browser. Showing default location (Seoul).');
        console.log("Geolocation is not available in this browser.");
        // If geolocation is not available, load rooms for the default location (Seoul)
        loadNearbyRooms(37.5665, 126.9780);
    }

    // Function to create a custom icon for the user's location
    function createCustomIcon() {
        return L.divIcon({
            className: 'user-location-icon',
            html: '<div style="background-color: #4a8af4; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
            iconSize: [20, 20],
        });
    }

    // Handle map right-click to create a new chat room
    map.on('contextmenu', (e) => {
        const { lat, lng } = e.latlng;
        const formHtml = `
            <h4>Create New Chat Room</h4>
            <input type="text" id="chat-room-name" placeholder="Enter room name" required />
            <button id="create-room-btn">Create</button>
        `;

        const popup = L.popup()
            .setLatLng(e.latlng)
            .setContent(formHtml)
            .openOn(map);

        // Must use event delegation or re-bind after popup is added to DOM
        // A simpler way for this context is to get the element right after setting content
        const createBtn = document.getElementById('create-room-btn');
        createBtn.onclick = async () => {
            const roomNameInput = document.getElementById('chat-room-name');
            const roomName = roomNameInput.value;
            if (roomName) {
                try {
                    const newRoom = await createChatRoom(roomName, lat, lng);
                    map.closePopup();
                    L.marker([newRoom.location.lat, newRoom.location.lng])
                        .addTo(map)
                        .bindPopup(`<b>${newRoom.name}</b><br><button onclick="joinChat(${newRoom.id})">Join</button>`)
                        .openPopup();
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            } else {
                alert('Please enter a room name.');
            }
        };
    });
});

// Placeholder for join chat functionality
function joinChat(roomId) {
    window.location.href = `/chat/${roomId}`;
}
