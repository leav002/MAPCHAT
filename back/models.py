from .db import db
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

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
    chat_participations = db.relationship('ChatParticipant', backref='user', lazy=True)

# ChatRoom 모델 정의
class ChatRoom(db.Model):
    __tablename__ = 'chat_room'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # 2. location 컬럼 변경 및 인덱스 추가
    location = db.Column(
        Geometry('POINT', srid=4326), 
        nullable=False, 
        spatial_index=True  # 3. 공간 인덱스를 컬럼 정의에 포함
    )
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    active_until = db.Column(db.DateTime, nullable=True) # Expiration time
    last_message_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # 관계 설정
    messages = db.relationship('Message', backref='room', lazy=True, cascade="all, delete-orphan")
    participants = db.relationship('ChatParticipant', backref='room', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        from geoalchemy2.shape import to_shape
        point = to_shape(self.location)
        # MySQL SRID 4326: POINT(위도 경도) 순서 저장 → point.x=위도, point.y=경도
        return {
            'id': self.id,
            'name': self.name,
            'location': {
                'lat': point.x,
                'lng': point.y
            },
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'participant_count': len(self.participants)
        }

# Message 모델 정의
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
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