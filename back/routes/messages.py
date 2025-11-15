from flask import Blueprint, session
from flask_socketio import emit, join_room
from .. import db
from ..models import Message, ChatParticipant, User
from ..socket import socketio

messages_bp = Blueprint('messages', __name__)

@socketio.on('join')
def on_join(data):
    """User joins a chat room"""
    if 'user_id' not in session:
        return # Ignore if user is not logged in

    user_id = session['user_id']
    room_id = data.get('room_id')
    if not room_id:
        return

    # Add user to the SocketIO room
    join_room(room_id)

    # Check if user is already a participant
    participant = ChatParticipant.query.filter_by(
        user_id=user_id,
        room_id=room_id
    ).first()

    # If not, add them to the participants table
    if not participant:
        new_participant = ChatParticipant(user_id=user_id, room_id=room_id)
        db.session.add(new_participant)
        db.session.commit()

    # Announce that a user has joined the room
    username = session.get('username', 'A user')
    emit('status', {'msg': f'{username} has entered the room.'}, room=room_id)


@socketio.on('send_message')
def on_send_message(data):
    """User sends a message"""
    if 'user_id' not in session:
        return # Ignore if user is not logged in

    user_id = session['user_id']
    room_id = data.get('room_id')
    text = data.get('text')

    if not room_id or not text:
        return

    # Create and save the message
    new_message = Message(user_id=user_id, room_id=room_id, text=text)
    db.session.add(new_message)
    db.session.commit()

    # Fetch user details for the response
    user = User.query.get(user_id)

    # Broadcast the message to all users in the room
    emit('new_message', {
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname
        },
        'text': new_message.text,
        'created_at': new_message.created_at.isoformat()
    }, room=room_id)
