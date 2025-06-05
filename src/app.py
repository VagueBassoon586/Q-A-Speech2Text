from re import search
from dotenv import load_dotenv
from os import getenv
from os.path import dirname, realpath
from random import shuffle, randint
from flask import Flask, request, jsonify, send_from_directory, render_template
from speech import Speech2Txt
# from time import sleep
import tempfile
import websockets
import asyncio
import ffmpeg

app = Flask(__name__, template_folder = "../templates", static_folder = "../templates/static")

# Serve the static frontend
@app.route('/')
def index():
	return render_template("index.html")

# Handle event when all questions have been asked
@app.route('/question')
def question():
	global lstQA, ind
	if ind >= len(lstQA):
		return jsonify({'question': "No more questions!"})
	q = lstQA[ind][0]
	return jsonify({'question': q})

@app.route('/answer', methods=['POST'])
def answer():
	global ind, lstQA
	if ind >= len(lstQA):
		return jsonify({'correct': False, 'transcript': '', 'message': 'No more questions.'})
	f = request.files['audio']

	# Save input file from user input as .wav
	with tempfile.NamedTemporaryFile(delete = False, suffix = ".wav") as tmp_in:
		f.save(tmp_in.name)
		# Output file for standardized audio (16kb/s, mono channel, 16kHz)
		with tempfile.NamedTemporaryFile(delete = False, suffix = ".wav") as tmp_out:
			(ffmpeg.input(tmp_in.name).output(tmp_out.name, ac = 1, ar = 16000, sample_fmt = 's16').overwrite_output().run(quiet = True))
			transcript = Speech2Txt(tmp_out.name, False)

	# Check answer and send result
	res = checkAnswer(transcript)
	asyncio.run(sendResult(teams[randint(0, 5)], res, transcript))
	ind += 1
	return jsonify({'correct': res, 'transcript': transcript})

# === Step 1: Load Teams, Questions and Answers from Server ===
def retrieveData():
	global lstQA, teams
	path = dirname(realpath(__file__)).replace('src', 'data')
	lstQA = [[q.strip(), a.strip()] for q, a in zip(open(f"{path}/Questions.in", "r", encoding="utf-8").readlines(), open(f"{path}/Answers.in", "r", encoding="utf-8").readlines())]
	teams = [t.strip() for t in open(f"{path}/Teams.in", "r", encoding = "utf-8").readlines()]
	return teams, lstQA

# === Step 2: Check for right and wront answers ===
def checkAnswer(input):
	global lstQA, teams, ind
	poAns = [a.lower() for a in lstQA[ind][1].split(',')]
	for ans in poAns:
		res = bool(search(ans, input))
		if res:
			ind += 1
			return True
	return False

# === Step 3: Send result to Robot ===
async def sendResult(team, res, inp):
	load_dotenv()
	result = f"{team}_{lstQA[ind][0]}_{inp}_{res}" # type: ignore
	async with websockets.connect(str(getenv("NGROK_URL"))) as websocket:
		await websocket.send(result)


if __name__ == '__main__':
	# Initialize varible
	teams, lstQA = retrieveData()
	ind = 0
	# Randomize questions
	shuffle(lstQA)
	app.run(debug = True)

	# # For debugging:
	# team = input("Nhập tên đội: ")
	# while (team not in teams):
	# 	teams = input("Vui lòng nhập lại tên đội: ")
	# print(f"Câu hỏi của bạn:\n{lstQA[ind][0]}")
	# for i in range(5, 0, -1):
	# 	print(f"\rTrả lời sau: {i}", end = '', flush = True)
	# 	sleep(1)
	# print("\r", end = '', flush = True)
	# print("Vui lòng đọc trả lời: ")
	# inp = Speech2Txt("", True)
	# print(f"Câu trả lời của bạn: {inp}")
	# res = checkAnswer(inp.lower())
	# print(res)
	# asyncio.run(sendResult("ws://localhost:8765", team, res, inp))