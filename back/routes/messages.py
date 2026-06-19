from flask import Blueprint, session, request
from flask_socketio import emit, join_room
from sqlalchemy import select, func
from ..db import db
from ..models import Message, ChatParticipant, User, ChatRoom
from ..socket_io import socketio
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@socketio.on('join')
def on_join(data):
    user_id = session.get('user_id') or data.get('user_id')
    if not user_id:
        return

    room_id = data.get('room_id')
    if not room_id:
        return

    join_room(room_id)

    participant = ChatParticipant.query.filter_by(user_id=user_id, room_id=room_id).first()
    if not participant:
        db.session.add(ChatParticipant(user_id=user_id, room_id=room_id))
        db.session.commit()

    username = session.get('username') or (User.query.get(user_id).nickname if user_id else '사용자')
    emit('status', {'msg': f'{username}님이 입장하셨습니다.'}, room=room_id)


@socketio.on('send_message')
def on_send_message(data):
    user_id = session.get('user_id') or data.get('user_id')
    if not user_id:
        return
    room_id = data.get('room_id')
    text = data.get('text')
    image_data = data.get('image')
    lat = data.get('lat')
    lng = data.get('lng')

    if not room_id or (not text and not image_data):
        return

    # 거리 검증 (위치 정보가 있을 때만)
    if lat and lng:
        try:
            user_loc = func.ST_GeomFromText(f'POINT({lat} {lng})', 4326)
            dist = db.session.scalar(
                select(func.ST_Distance_Sphere(ChatRoom.location, user_loc))
                .where(ChatRoom.id == room_id)
            )
            if dist is not None and dist > 500:
                emit('error', {'msg': f'방과의 거리가 너무 멉니다 ({int(dist)}m, 500m 이내만 가능).'})
                return
        except Exception as e:
            print(f"[거리 검증 오류] {e}")

    # 메시지 저장
    new_message = Message(
        user_id=user_id,
        room_id=room_id,
        text=text,
        image_url=image_data
    )
    db.session.add(new_message)
    db.session.commit()

    user = User.query.get(user_id)

    # 브로드캐스트
    emit('new_message', {
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname
        },
        'text': new_message.text,
        'image': new_message.image_url,
        'created_at': datetime.now().isoformat()
    }, room=room_id)
