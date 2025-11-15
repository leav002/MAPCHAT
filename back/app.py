import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .db import db
from .socket import socketio
from .models import User, ChatRoom, ChatParticipant, Message
from .routes.messages import messages_bp
from geoalchemy2.elements import WKTElement
from sqlalchemy.sql import func

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), '../front'),
            static_folder=os.path.join(os.path.dirname(__file__), '../front'))

# 세션 및 CSRF 보호를 위한 시크릿 키 설정
app.config['SECRET_KEY'] = 'dev' # 개발용 임시 키입니다. 배포 시에는 강력한 키로 변경해야 합니다.

DB_USER = "root"
DB_PASSWORD = "111111"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "mapchat"
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio.init_app(app)

# Register Blueprints
app.register_blueprint(messages_bp)

@app.route('/')
def index():
    user = None
    joined_rooms = []
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        # Eager load the 'room' relationship to avoid N+1 queries in the template
        participations = db.session.query(ChatParticipant).filter_by(user_id=user.id).options(
            db.joinedload(ChatParticipant.room)
        ).all()
        joined_rooms = [p.room for p in participations]
        
    return render_template('index.html', user=user, joined_rooms=joined_rooms)

@app.route('/map')
def map_page():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('pages/map.html', user=user)

@app.route('/chat/<int:room_id>')
def chat_room(room_id):
    if 'user_id' not in session:
        return redirect(url_for('sign_in'))
    
    room = ChatRoom.query.get_or_404(room_id)
    # Eagerly load authors to prevent N+1 query problem in template
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at.asc()).all()
    
    return render_template('pages/chat.html', room=room, messages=messages)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            return redirect(url_for('sign_in'))
            
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('index'))
        
    return render_template('pages/login.html')

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        nickname = request.form.get('nickname')
        password = request.form.get('password')

        # 사용자 이름 또는 닉네임 중복 확인
        if User.query.filter((User.username == username) | (User.nickname == nickname)).first():
            return redirect(url_for('sign_up'))

        # 비밀번호 해싱 및 사용자 생성
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, nickname=nickname, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('sign_in'))

    return render_template('pages/signup.html')

@app.route('/test_db')
def test_db():
    try:
        with app.app_context():
            user_count = db.session.query(User).count()
        return f"데이터베이스 연결 성공! 현재 사용자 수: {user_count}"
    except Exception as e:
        return f"데이터베이스 연결 실패: {e}"

@app.route('/api/chat-rooms', methods=['GET'])
def get_chat_rooms():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if lat is None or lng is None:
        return jsonify({'error': 'Missing required query parameters: lat, lng'}), 400

    # 사용자의 현재 위치를 WKT로 변환
    user_location = WKTElement(f'POINT({lng} {lat})', srid=4326)

    # 1km 반경 내의 채팅방 검색 (미터 단위)
    radius = 1000
    
    # ST_DWithin을 사용하여 공간 쿼리 실행
    nearby_rooms = db.session.query(ChatRoom).filter(
        func.ST_DWithin(ChatRoom.location, user_location, radius)
    ).all()

    # 결과를 JSON으로 직렬화
    rooms_list = []
    for room in nearby_rooms:
        # location 컬럼에서 위도, 경도 추출
        # MySQL에서 ST_AsText는 'POINT(lng lat)' 형식을 반환합니다.
        point_text = db.session.scalar(room.location.ST_AsText())
        coords = point_text.replace('POINT(', '').replace(')', '').split()
        lng, lat = map(float, coords)

        rooms_list.append({
            'id': room.id,
            'name': room.name,
            'location': {'lat': lat, 'lng': lng},
            'created_by': room.created_by,
            'created_at': room.created_at.isoformat()
        })

    return jsonify(rooms_list)

@app.route('/api/chat-rooms', methods=['POST'])
def create_chat_room():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data or 'name' not in data or 'lat' not in data or 'lng' not in data:
        return jsonify({'error': 'Missing required fields: name, lat, lng'}), 400

    creator_id = session['user_id']
    
    # WKT(Well-Known Text) 형식으로 POINT 데이터 생성 (SRID 4326)
    location_wkt = WKTElement(f'POINT({data["lng"]} {data["lat"]})', srid=4326)

    new_room = ChatRoom(
        name=data['name'],
        location=location_wkt,
        created_by=creator_id
    )

    db.session.add(new_room)
    db.session.flush()  # new_room.id 값을 가져오기 위해 flush
 
    # 채팅방 생성자를 참여자로 추가
    new_participant = ChatParticipant(
        room_id=new_room.id,
        user_id=creator_id
    )
    
    db.session.add(new_participant)
    db.session.commit()

    return jsonify({
        'id': new_room.id,
        'name': new_room.name,
        'location': {
            'lat': data['lat'],
            'lng': data['lng']
        },
        'created_by': new_room.created_by,
        'created_at': new_room.created_at.isoformat()
    }), 201


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, port=5001)