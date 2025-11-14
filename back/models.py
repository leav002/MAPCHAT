from db import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import POINT

# User 모델 정의
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('user', 'admin'), nullable=False, default='user')
    status = db.Column(db.Enum('active', 'banned'), nullable=False, default='active')
    created_at = db.Column(db.DateTime, server_default=func.now())

    # 관계 설정
    created_chat_rooms = db.relationship('ChatRoom', backref='creator', lazy=True)
    messages = db.relationship('Message', backref='author', lazy=True)

# ChatRoom 모델 정의
class ChatRoom(db.Model):
    __tablename__ = 'chat_room'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # lat, lng 대신 location 사용
    location = db.Column(POINT, nullable=False) # 2. 컬럼 변경
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    # 관계 설정
    messages = db.relationship('Message', backref='room', lazy=True, cascade="all, delete-orphan")
    participants = db.relationship('ChatParticipant', backref='room', lazy=True, cascade="all, delete-orphan")

    # SQLAlchemy에서 공간 인덱스 지정
    __table_args__ = (
        db.SpatialIndex('idx_location', location, mysql_using='BTREE'), # 3. 인덱스 추가
    )

# Message 모델 정의
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

# ChatParticipant 모델 정의
class ChatParticipant(db.Model):
    __tablename__ = 'chat_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, server_default=func.now())
    left_at = db.Column(db.DateTime, nullable=True)
    
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id'),)