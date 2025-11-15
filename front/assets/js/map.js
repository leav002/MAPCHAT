document.addEventListener('DOMContentLoaded', () => {
    kakao.maps.load(() => {
        const mapContainer = document.getElementById('map');
        let map; // Will be initialized later
        let userMarker; // To store the user's location marker
        let userAccuracyCircle; // To store the accuracy circle

        // Function to fetch and display chat rooms
        async function loadNearbyRooms(lat, lng) {
            const rooms = await fetchNearbyChatRooms(lat, lng);
            rooms.forEach(room => {
                const roomPosition = new kakao.maps.LatLng(room.location.lat, room.location.lng);

                // Create a marker for the chat room
                const marker = new kakao.maps.Marker({
                    position: roomPosition
                });
                marker.setMap(map);

                // Create an info window for the marker
                const iwContent = `
                    <div style="padding:5px; width: 150px; text-align: center;">
                        <b>${room.name}</b><br>
                        <button onclick="joinChat(${room.id})" style="margin-top: 5px; padding: 3px 7px; cursor: pointer;">Join</button>
                    </div>`;
                const infowindow = new kakao.maps.InfoWindow({
                    content: iwContent
                });

                // Add click listener to open the info window
                kakao.maps.event.addListener(marker, 'click', function () {
                    infowindow.open(map, marker);
                });
            });
        }

        // Function to display a marker and accuracy circle for the user's location
        function displayUserMarker(lat, lng, accuracy) {
            const userPosition = new kakao.maps.LatLng(lat, lng);

            // If a user marker already exists, update its position
            if (userMarker) {
                userMarker.setPosition(userPosition);
            } else {
                // Create a new marker for the user
                userMarker = new kakao.maps.Marker({
                    position: userPosition,
                });
                userMarker.setMap(map);
            }

            // If an accuracy circle already exists, update its position and radius
            if (userAccuracyCircle) {
                userAccuracyCircle.setPosition(userPosition);
                userAccuracyCircle.setRadius(accuracy);
            } else {
                // Create a new circle to show the accuracy
                userAccuracyCircle = new kakao.maps.Circle({
                    center: userPosition,
                    radius: accuracy, // radius in meters
                    strokeWeight: 1,
                    strokeColor: '#007BFF',
                    strokeOpacity: 0.8,
                    fillColor: '#007BFF',
                    fillOpacity: 0.15
                });
                userAccuracyCircle.setMap(map);
            }

            // Center the map on the user's location
            map.setCenter(userPosition);
        }

        // Initialize the map
        function initMap(lat, lng) {
            const options = {
                center: new kakao.maps.LatLng(lat, lng),
                level: 4 // Zoom level
            };
            map = new kakao.maps.Map(mapContainer, options);

            // Add right-click event listener to the map
            kakao.maps.event.addListener(map, 'rightclick', function (mouseEvent) {
                const latlng = mouseEvent.latLng;

                const formHtml = `
                    <div style="padding:10px; width: 250px;">
                        <h4>Create New Chat Room</h4>
                        <input type="text" id="chat-room-name" placeholder="Enter room name" required style="width: 95%; margin-bottom: 5px;" />
                        <button id="create-room-btn" style="width: 100%; padding: 5px 0; cursor: pointer;">Create</button>
                    </div>
                `;

                const infowindow = new kakao.maps.InfoWindow({
                    content: formHtml,
                    position: latlng
                });
                infowindow.open(map);

                setTimeout(() => {
                    const createBtn = document.getElementById('create-room-btn');
                    if (createBtn) {
                        createBtn.onclick = async () => {
                            const roomNameInput = document.getElementById('chat-room-name');
                            const roomName = roomNameInput.value;
                            if (roomName) {
                                try {
                                    const newRoom = await createChatRoom(roomName, latlng.getLat(), latlng.getLng());
                                    infowindow.close();
                                    loadNearbyRooms(latlng.getLat(), latlng.getLng());
                                } catch (error) {
                                    alert(`Error: ${error.message}`);
                                }
                            } else {
                                alert('Please enter a room name.');
                            }
                        };
                    }
                }, 100);
            });
        }

        // --- Main Execution ---

        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude, accuracy } = position.coords;
                    initMap(latitude, longitude);
                    displayUserMarker(latitude, longitude, accuracy);
                    loadNearbyRooms(latitude, longitude);
                },
                (error) => {
                    console.error("Error getting user's location:", error);
                    alert('Could not determine your location. Showing default location (Seoul).');
                    const defaultLat = 37.5665;
                    const defaultLng = 126.9780;
                    initMap(defaultLat, defaultLng);
                    loadNearbyRooms(defaultLat, defaultLng);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 } // Options for geolocation
            );
        } else {
            alert('Geolocation is not available in this browser. Showing default location (Seoul).');
            const defaultLat = 37.5665;
            const defaultLng = 126.9780;
            initMap(defaultLat, defaultLng);
            loadNearbyRooms(defaultLat, defaultLng);
        }
    });
});

// This function is called from the InfoWindow content
function joinChat(roomId) {
    window.location.href = `/chat/${roomId}`;
}