from back.app import app, socketio

if __name__ == '__main__':
    socketio.run(app, debug=False, port=5001)
