import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .db import db
from .socket_io import socketio
from .models import User, ChatRoom, ChatParticipant, Message
from .routes.messages import messages_bp
from sqlalchemy import select
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# 경로를 아주 명확하게 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FRONT_DIR = os.path.join(ROOT_DIR, 'front')

app = Flask(__name__,
            template_folder=FRONT_DIR,
            static_folder=FRONT_DIR,
            static_url_path='/static')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    

db.init_app(app)
socketio.init_app(app)
app.register_blueprint(messages_bp)

@app.route('/')
def index():
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    joined_rooms = []
    if user:
        participations = ChatParticipant.query.filter_by(user_id=user.id).all()
        now = datetime.now()
        joined_rooms = [p.room for p in participations if p.room and (p.room.active_until is None or p.room.active_until > now)]
    return render_template('index.html', user=user, joined_rooms=joined_rooms)

@app.route('/map')
def map_page():
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('pages/map.html', user=user)

@app.route('/chat/<int:room_id>')
def chat_room(room_id):
    if 'user_id' not in session: return redirect(url_for('sign_in'))
    room = ChatRoom.query.get_or_404(room_id)
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at.asc()).all()
    return render_template('pages/chat.html', room=room, messages=messages)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['user_id'], session['username'], session['nickname'] = user.id, user.username, user.nickname
            return redirect(url_for('index'))
        flash('로그인 실패', 'error')
    return render_template('pages/login.html')

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('아이디 중복', 'error'); return redirect(url_for('sign_up'))
        new_user = User(username=request.form.get('username'), nickname=request.form.get('nickname'), 
                        password=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256'))
        db.session.add(new_user); db.session.commit()
        return redirect(url_for('sign_in'))
    return render_template('pages/signup.html')

@app.route('/api/chat-rooms', methods=['GET'])
def get_chat_rooms():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if lat is None or lng is None:
        return jsonify([])
    user_location = func.ST_GeomFromText(f'POINT({lat} {lng})', 4326)
    try:
        rooms = ChatRoom.query.filter(
            func.ST_Distance_Sphere(ChatRoom.location, user_location) <= 2000
        ).all()
        return jsonify([room.to_dict() for room in rooms])
    except Exception as e:
        print(f'[get_chat_rooms 오류] {e}')
        return jsonify([])


@app.route('/api/nearby-rooms', methods=['GET'])
def get_nearby_rooms():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if lat is None or lng is None:
        return jsonify([])

    joined_ids = set()
    if 'user_id' in session:
        joined_ids = {p.room_id for p in ChatParticipant.query.filter_by(user_id=session['user_id']).all()}

    user_loc = func.ST_GeomFromText(f'POINT({lat} {lng})', 4326)
    dist_expr = func.ST_Distance_Sphere(ChatRoom.location, user_loc)
    try:
        rows = db.session.execute(
            select(ChatRoom, dist_expr.label('distance'))
            .where(dist_expr <= 1000)
            .order_by(dist_expr)
        ).all()
    except Exception as e:
        print(f'[get_nearby_rooms 오류] {e}')
        return jsonify([])

    result = []
    for room, dist in rows:
        if room.id in joined_ids:
            continue
        room_dict = room.to_dict()
        room_dict['distance'] = round(dist) if dist is not None else None
        result.append(room_dict)

    return jsonify(result)

@app.route('/api/my-rooms', methods=['GET'])
def get_my_rooms():
    if 'user_id' not in session:
        return jsonify([])
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    participations = ChatParticipant.query.filter_by(user_id=session['user_id']).all()
    now = datetime.now()
    rooms = [p.room for p in participations if p.room and (p.room.active_until is None or p.room.active_until > now)]

    result = []
    for room in rooms:
        room_dict = room.to_dict()
        if lat is not None and lng is not None:
            try:
                user_loc = func.ST_GeomFromText(f'POINT({lat} {lng})', 4326)
                dist = db.session.scalar(
                    select(func.ST_Distance_Sphere(ChatRoom.location, user_loc))
                    .where(ChatRoom.id == room.id)
                )
                room_dict['distance'] = round(dist) if dist is not None else None
            except Exception:
                room_dict['distance'] = None
        else:
            room_dict['distance'] = None
        result.append(room_dict)

    if lat is not None and lng is not None:
        result.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))

    return jsonify(result)


@app.route('/api/chat-rooms', methods=['POST'])
def create_chat_room():
    if 'user_id' not in session: return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json()
    geom = func.ST_GeomFromText(f'POINT({data["lat"]} {data["lng"]})', 4326)
    new_room = ChatRoom(name=data['name'], location=geom, created_by=session['user_id'], active_until=datetime.now() + timedelta(hours=24))
    db.session.add(new_room); db.session.flush()
    db.session.add(ChatParticipant(room_id=new_room.id, user_id=session['user_id']))
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    socketio.run(app, debug=True, port=5001)
