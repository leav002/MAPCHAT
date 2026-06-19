import eventlet
eventlet.monkey_patch()

from back.app import app, socketio

if __name__ == '__main__':
    socketio.run(app, debug=False, port=5001)
