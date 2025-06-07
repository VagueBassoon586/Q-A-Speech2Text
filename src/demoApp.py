from re import search
from dotenv import load_dotenv
from os import getenv
from flask import Flask, request, jsonify, render_template
from speech import Speech2Txt
# from time import sleep
import tempfile
import websockets
import asyncio
import ffmpeg
import threading

app = Flask(__name__, template_folder = "../templates", static_folder = "../templates/static")

# Serve the static frontend
@app.route('/')
def index():
	return render_template("index.html")

# Handle event when all questions have been asked
@app.route('/question')
def question():
	global Q, A
	if Q == "" or A == "":
		return jsonify({'question': "No more questions!"})
	return jsonify({'question': Q})

@app.route('/answer', methods=['POST'])
def answer():
	if Q == "" or A == "":
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
	asyncio.run(sendResult(res, transcript))
	return jsonify({'correct': res, 'transcript': transcript})

# === Step 1: Load Teams, Questions and Answers from Server ===
async def retrieveData():
	load_dotenv()
	async with websockets.connect(str(getenv("NGROK_URL"))) as websocket:
		result = (await websocket.recv()).split("_") # type: ignore
		global Q, A
		Q, A = result[0], result[1]
		print(Q, A)

# === Step 2: Check for right and wront answers ===
def checkAnswer(input):
	global A
	poAns = [a.lower() for a in A.split(',')] # type: ignore
	for ans in poAns:
		res = bool(search(ans, input))
		if res:
			return True
	return False

# === Step 3: Send result to Robot ===
async def sendResult(res, inp):
	load_dotenv()
	result = f"{Q}_{res}_{inp}" # type: ignore
	async with websockets.connect(str(getenv("NGROK_URL"))) as websocket:
		await websocket.send(result)


if __name__ == '__main__':
	# Initialize varible
	Q, A = "", ""
	t = threading.Thread(target = retrieveData, daemon=True)
	t.start()
	app.run(debug=True)

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
	# asyncio.run(sendResult("wss://informed-legally-weasel.ngrok-free.app", team, res, inp))