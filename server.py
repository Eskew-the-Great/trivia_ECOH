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
{"question": "What is the main vision of the Ethiopian Community Organization in Houston (ECOH)?",
 "options": ["To build a strong, vibrant, and united Ethiopian community integrated into the larger community while preserving cultural heritage",
             "To organize cultural events only",
             "To create a small network of professionals",
             "To focus only on the economic development of Ethiopian businesses"],
 "answer": "To build a strong, vibrant, and united Ethiopian community integrated into the larger community while preserving cultural heritage"},
{"question": "Which of the following is NOT one of ECOH's four key mission words?",
 "options": ["Entertain", "Educate", "Engage", "Empower"],
 "answer": "Entertain"},
{"question": "What does ECOH aim to do in its mission to 'educate' the community?",
 "options": ["Increase community awareness in all matters that affect the community",
             "Provide entertainment events",
             "Focus only on youth programs",
             "Create business networking opportunities"],
 "answer": "Increase community awareness in all matters that affect the community"},
{"question": "According to ECOH's core values, what does 'Compassion' mean?",
 "options": ["Always strive to serve the community with utmost respect and sensitivity",
             "Always give financial support",
             "Always prioritize large donors",
             "Always host cultural festivals"],
 "answer": "Always strive to serve the community with utmost respect and sensitivity"},
{"question": "Which of these is part of ECOH's Core Values?",
 "options": ["All of the above", "Accountability", "Integrity", "Compassion"],
 "answer": "All of the above"},
{"question": "Which value reflects ECOH's commitment to being answerable to the community?",
 "options": ["Accountability", "Inclusivity", "Leadership", "Sustainability"],
 "answer": "Accountability"},
{"question": "What does ECOH strive to achieve by 'engaging' community members?",
 "options": ["Identifying needs and developing programs for advancement",
             "Hosting regular fundraisers",
             "Providing personal loans",
             "Hiring more staff"],
 "answer": "Identifying needs and developing programs for advancement"},
{"question": "How does ECOH plan to 'empower' community members?",
 "options": ["By providing resources and tools to build a strong foundation for future generations",
             "By creating exclusive clubs",
             "By focusing only on senior members",
             "By organizing monthly parties"],
 "answer": "By providing resources and tools to build a strong foundation for future generations"},
{"question": "What does ECOH mean by 'enriching' the community?",
 "options": ["Culturally and socially becoming vibrant and active members of the larger community",
             "Focusing only on economic growth",
             "Hosting weekly sports tournaments",
             "Providing entertainment only"],
 "answer": "Culturally and socially becoming vibrant and active members of the larger community"},
{"question": "What is the organization's approach to inclusivity?",
 "options": ["Strive to equally serve all Ethiopians in the community",
             "Prioritize new immigrants only",
             "Serve based on financial contribution",
             "Focus only on Houston residents"],
 "answer": "Strive to equally serve all Ethiopians in the community"},
{"question": "What is the capital city of Ethiopia?",
 "options": ["Addis Ababa", "Gondar", "Dire Dawa", "Mekelle"],
 "answer": "Addis Ababa"},
{"question": "Which famous landmark is known as one of the 'New 7 Wonders of the World' and located in Ethiopia?",
 "options": ["The Rock-Hewn Churches of Lalibela",
             "The Pyramids of Axum",
             "The Great Wall of Harar",
             "Simien Mountains"],
 "answer": "The Rock-Hewn Churches of Lalibela"},
{"question": "What is the national language of Ethiopia?",
 "options": ["Amharic", "Oromo", "Tigrinya", "Afar"],
 "answer": "Amharic"},
{"question": "Which Ethiopian long-distance runner won two Olympic gold medals and is considered one of the greatest of all time?",
 "options": ["Haile Gebrselassie", "Kenenisa Bekele", "Derartu Tulu", "Mamo Wolde"],
 "answer": "Haile Gebrselassie"},
{"question": "Which ancient kingdom is often referred to as one of the great civilizations of early Africa and located in present-day Ethiopia?",
 "options": ["Axumite Kingdom", "Mali Empire", "Ghana Empire", "Songhai Empire"],
 "answer": "Axumite Kingdom"},
{"question": "Which of the following is a traditional Ethiopian coffee ceremony called?",
 "options": ["Buna", "Tej", "Injera", "Tella"],
 "answer": "Buna"},
{"question": "What is the name of the flat, sourdough-risen bread that is a staple in Ethiopian cuisine?",
 "options": ["Injera", "Doro Wat", "Tibs", "Kitfo"],
 "answer": "Injera"},
{"question": "Which unique calendar does Ethiopia use that differs from the Western (Gregorian) calendar?",
 "options": ["Ethiopian Calendar", "Hijri", "Julian Calendar", "Lunar Calendar"],
 "answer": "Ethiopian Calendar"},
{"question": "Which Ethiopian city is considered one of the oldest continuously inhabited cities in the world?",
 "options": ["Harar", "Addis Ababa", "Bahir Dar", "Dire Dawa"],
 "answer": "Harar"},
{"question": "What unique alphabet and writing system is used in the Ethiopian language?",
 "options": ["Ge'ez (Fidel)", "Latin", "Arabic", "Cyrillic"],
 "answer": "Ge'ez (Fidel)"}
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
