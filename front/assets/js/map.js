document.addEventListener('DOMContentLoaded', () => {
    console.log("Map JS Loaded");
    if (typeof kakao === 'undefined') {
        console.error("Kakao Maps API not loaded!");
        return;
    }
    kakao.maps.load(() => {
        console.log("Kakao Maps Load Callback");
        const mapContainer = document.getElementById('map');
        let map;

        let userMarker;
        let userAccuracyCircle;
        let creationInfoWindow;
        let currentUserPosition;
        let markers = []; // Track markers to prevent duplicates

        // UI elements
        const createRoomBtn = document.createElement('button');
        createRoomBtn.id = 'floating-create-btn';
        createRoomBtn.innerHTML = '+';
        createRoomBtn.title = '현재 위치에 채팅방 생성';
        document.body.appendChild(createRoomBtn);

        createRoomBtn.addEventListener('click', () => {
            if (!IS_LOGGED_IN) {
                alert('로그인이 필요합니다.');
                return;
            }
            if (!currentUserPosition) {
                alert('사용자 위치를 확인하는 중입니다.');
                return;
            }
            showCreationWindow(currentUserPosition);
        });

        async function loadNearbyRooms(lat, lng) {
            const rooms = await fetchNearbyChatRooms(lat, lng);
            
            // Clear existing markers
            markers.forEach(m => m.setMap(null));
            markers = [];

            rooms.forEach(room => {
                const roomPosition = new kakao.maps.LatLng(room.location.lat, room.location.lng);
                const marker = new kakao.maps.Marker({ position: roomPosition });
                marker.setMap(map);
                markers.push(marker);

                const iwContent = `
                    <div style="padding:10px; width: 180px; text-align: center; font-family: sans-serif;">
                        <b style="font-size: 1.1em;">${room.name}</b><br>
                        <span style="color: #666; font-size: 0.9em;">👥 참여자: ${room.participant_count}명</span><br>
                        <button onclick="joinChat(${room.id})" style="margin-top: 8px; padding: 5px 12px; cursor: pointer; background: #007BFF; color: white; border: none; border-radius: 4px;">입장하기</button>
                    </div>`;
                const infowindow = new kakao.maps.InfoWindow({ content: iwContent });

                kakao.maps.event.addListener(marker, 'click', () => {
                    if (creationInfoWindow) creationInfoWindow.close();
                    infowindow.open(map, marker);
                });
            });
        }

        function showCreationWindow(position) {
            if (creationInfoWindow) creationInfoWindow.close();

            const formHtml = `
                <div style="padding:15px; width: 220px; font-family: sans-serif;">
                    <h4 style="margin: 0 0 10px 0;">새 채팅방 만들기</h4>
                    <p style="font-size: 0.8em; color: #666; margin-bottom: 10px;">채팅방은 현재 내 위치에 생성됩니다.</p>
                    <input type="text" id="chat-room-name" placeholder="방 제목 입력" required style="width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;" />
                    <button id="create-room-btn-submit" style="width: 100%; padding: 8px 0; cursor: pointer; background: #28a745; color: white; border: none; border-radius: 4px;">만들기</button>
                </div>
            `;

            creationInfoWindow = new kakao.maps.InfoWindow({
                content: formHtml,
                position: position
            });
            creationInfoWindow.open(map);

            setTimeout(() => {
                const submitBtn = document.getElementById('create-room-btn-submit');
                if (submitBtn) {
                    submitBtn.onclick = async () => {
                        const roomName = document.getElementById('chat-room-name').value.trim();
                        if (roomName) {
                            try {
                                await createChatRoom(roomName, position.getLat(), position.getLng());
                                creationInfoWindow.close();
                                window.location.reload();
                            } catch (error) {
                                alert(`에러: ${error.message}`);
                            }
                        } else {
                            alert('방 제목을 입력해주세요.');
                        }
                    };
                }
            }, 100);
        }

        function displayUserMarker(lat, lng, accuracy) {
            const userPosition = new kakao.maps.LatLng(lat, lng);
            currentUserPosition = userPosition;

            if (userMarker) {
                userMarker.setPosition(userPosition);
            } else {
                userMarker = new kakao.maps.Marker({ position: userPosition });
                userMarker.setMap(map);
                map.setCenter(userPosition);
            }

            if (userAccuracyCircle) {
                userAccuracyCircle.setPosition(userPosition);
                userAccuracyCircle.setRadius(accuracy / 2);
            } else {
                userAccuracyCircle = new kakao.maps.Circle({
                    center: userPosition,
                    radius: accuracy / 2,
                    strokeWeight: 1,
                    strokeColor: '#007BFF',
                    strokeOpacity: 0.8,
                    fillColor: '#007BFF',
                    fillOpacity: 0.15
                });
                userAccuracyCircle.setMap(map);
            }
        }

        function initMap(lat, lng) {
            const options = {
                center: new kakao.maps.LatLng(lat, lng),
                level: 3
            };
            map = new kakao.maps.Map(mapContainer, options);

            // Right click for desktop as fallback
            kakao.maps.event.addListener(map, 'rightclick', (mouseEvent) => {
                if (!IS_LOGGED_IN) { alert('로그인이 필요합니다.'); return; }
                if (!currentUserPosition) { alert('위치를 확인 중입니다.'); return; }
                showCreationWindow(currentUserPosition);
            });
        }

        // --- 실시간 위치 추적 (watchPosition) ---
        if ('geolocation' in navigator) {
            let firstLocation = true;
            navigator.geolocation.watchPosition(
                (position) => {
                    const { latitude, longitude, accuracy } = position.coords;
                    if (firstLocation) {
                        initMap(latitude, longitude);
                        firstLocation = false;
                    }
                    displayUserMarker(latitude, longitude, accuracy);
                    loadNearbyRooms(latitude, longitude);
                },
                (error) => {
                    console.error("Location error:", error);
                    if (firstLocation) {
                        initMap(37.5665, 126.9780); // Seoul
                        loadNearbyRooms(37.5665, 126.9780);
                        firstLocation = false;
                    }
                },
                { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
            );
        } else {
            alert('이 브라우저는 위치 정보를 지원하지 않습니다.');
            initMap(37.5665, 126.9780);
        }
    });
});

function joinChat(roomId) {
    window.location.href = `/chat/${roomId}`;
}
