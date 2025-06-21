
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import threading
import eventlet
import time
import os

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

questions = [
    {"question": "Sample Question 1?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 2?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 3?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 4?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 5?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 6?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 7?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 8?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 9?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 10?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 11?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 12?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 13?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 14?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 15?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 16?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 17?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 18?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 19?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
    {"question": "Sample Question 20?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"},
]


players = {}
submitted = set()
question_timer = 15
question_order = []
current_question_index = 0

@app.route('/')
def index():
    return render_template('host.html')

@app.route('/player')
def player():
    return render_template('player.html')

@socketio.on('join')
def on_join(data):
    name = data['name']
    if name not in players:
        players[name] = 0
    emit('joined', {'msg': f"Welcome {name}!"})
    update_waiting_room()

@socketio.on('start_game')
def start_game():
    global current_question_index, question_order
    current_question_index = 0
    question_order = random.sample(range(len(questions)), len(questions))
    emit('game_start', broadcast=True)
    threading.Thread(target=run_quiz_loop).start()

def run_quiz_loop():
    global current_question_index, submitted
    while current_question_index < len(question_order):
        submitted.clear()
        q = questions[question_order[current_question_index]]
        socketio.emit('question', q)
        for remaining in range(question_timer, -1, -1):
            socketio.emit('timer', {'time': remaining})
            eventlet.sleep(1)
        correct_answer = q['answer']
        socketio.emit('reveal', {'answer': correct_answer})
        send_leaderboard()
        current_question_index += 1
        eventlet.sleep(3)
    socketio.emit('game_over', broadcast=True)

@socketio.on('submit_answer')
def handle_answer(data):
    global current_question_index
    name = data['name']
    answer = data['answer']
    if name in submitted:
        return
    submitted.add(name)
    correct_answer = questions[question_order[current_question_index]]['answer']
    if answer == correct_answer:
        players[name] += 1
    emit('acknowledge', {'correct': answer == correct_answer}, room=request.sid)

def send_leaderboard():
    sorted_scores = sorted(players.items(), key=lambda x: x[1], reverse=True)
    socketio.emit('leaderboard', {'scores': sorted_scores})

def update_waiting_room():
    socketio.emit('waiting', {'players': list(players.keys())})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
