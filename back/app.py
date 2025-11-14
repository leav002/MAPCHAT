import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from models import User

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

@app.route('/')
def index():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)