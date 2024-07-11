import json
import random
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta
from threading import Thread, Event

DEFAULT_DATA_FILE = 'language_data.json'
POPUP_INTERVAL = 60  # 1 minute
POPUP_WIDTH = 400
POPUP_HEIGHT = 150
POPUP_X = 1000  # Adjust based on screen resolution
POPUP_Y = 700   # Adjust based on screen resolution
ADD_WINDOW_WIDTH = 400
ADD_WINDOW_HEIGHT = 600
MAX_CONSECUTIVE_CORRECT = 10

stop_event = Event()
last_checked_date = None
data_file = DEFAULT_DATA_FILE
data = {}

# Load data from JSON file
def load_data(file_path):
    global last_checked_date
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            last_checked_date = datetime.strptime(data.get('last_checked_date', datetime.now().isoformat()), "%Y-%m-%d").date()
            return data
    except FileNotFoundError:
        last_checked_date = datetime.now().date()
        return {"words": [], "last_checked_date": last_checked_date.isoformat()}

# Save data to JSON file
def save_data(data, file_path):
    data['last_checked_date'] = last_checked_date.isoformat()
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Reset all 'today_consecutive_correct' when it's a new day
def reset_today_consecutive_correct(data):
    global last_checked_date
    current_date = datetime.now().date()
    if current_date != last_checked_date:
        for word in data['words']:
            word['today_consecutive_correct'] = 0
        last_checked_date = current_date

# Update the next test time based on performance
def schedule_next_test(word, response_time, correct):
    if 'today_consecutive_correct' not in word:
        word['today_consecutive_correct'] = 0

    if correct:
        word['consecutive_correct'] += 1
        word['today_consecutive_correct'] += 1
    else:
        word['consecutive_correct'] = 0
        word['today_consecutive_correct'] = 0

    word['times_tested'] += 1

    if word['today_consecutive_correct'] >= MAX_CONSECUTIVE_CORRECT:
        next_interval = timedelta(days=1)  # Push to the following day
        word['today_consecutive_correct'] = 0
    else:
        # Adjust interval based on performance
        if word['consecutive_correct'] >= 3:
            next_interval = timedelta(seconds=POPUP_INTERVAL * 4)
        elif word['consecutive_correct'] == 2:
            next_interval = timedelta(seconds=POPUP_INTERVAL * 2)
        elif response_time < 5:  # 5 seconds
            next_interval = timedelta(seconds=POPUP_INTERVAL * 1.5)
        else:
            next_interval = timedelta(seconds=POPUP_INTERVAL)

    word['next_test_time'] = (datetime.now() + next_interval).isoformat()

# Check user input and update progress
def check_answer(word, user_input, response_time):
    correct = user_input.strip().lower() == word['answer'].strip().lower()
    schedule_next_test(word, response_time, correct)
    return correct

# Show the popup
def show_popup(word):
    start_time = time.time()  # Record the time when the popup appears

    def on_submit(event=None):
        response_time = time.time() - start_time  # Calculate the response time in seconds
        user_input = entry.get()
        if check_answer(word, user_input, response_time):
            result_label.config(text="Correct!")
        else:
            result_label.config(text=f"Try again! Correct answer: {word['answer']}")
        save_data(data, data_file)
        root.after(2000, root.destroy)  # Close after 2 seconds

    root = tk.Tk()
    root.title("Language Study")
    root.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}+{POPUP_X}+{POPUP_Y}")
    root.attributes('-topmost', True)

    prompt_label = tk.Label(root, text=word['prompt'], wraplength=POPUP_WIDTH - 20)
    prompt_label.pack(pady=10)
    entry = tk.Entry(root)
    entry.pack(pady=5)
    entry.bind("<Return>", on_submit)  # Bind Enter key to submit
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=5)
    result_label = tk.Label(root, text="")
    result_label.pack(pady=5)
    root.mainloop()

# Trigger the popup at regular intervals
def start_popup_timer():
    while not stop_event.is_set():
        reset_today_consecutive_correct(data)
        now = datetime.now().isoformat()
        due_words = [word for word in data['words'] if word['next_test_time'] <= now]
        if due_words:
            # Sort due_words by consecutive_correct and next_test_time
            due_words.sort(key=lambda word: (word['consecutive_correct'], word['next_test_time']))
            cutoff = len(due_words) // 2
            filtered_words = due_words[:cutoff]
            print([word['answer'] for word in filtered_words])
            word = random.choice(filtered_words)
            show_popup(word)
        stop_event.wait(POPUP_INTERVAL)

# Interface to add new words and prompts
def add_word(prompt, answer):
    new_word = {
        "prompt": prompt,
        "answer": answer,
        "times_tested": 0,
        "consecutive_correct": 0,
        "today_consecutive_correct": 0,
        "next_test_time": datetime.now().isoformat()
    }
    data['words'].append(new_word)
    save_data(data, data_file)

# Function to open the add words window
def open_add_words_window():
    def add_words():
        for prompt, answer in zip(prompts_entry.get("1.0", tk.END).strip().split("\n"), answers_entry.get("1.0", tk.END).strip().split("\n")):
            add_word(prompt, answer)
        add_window.destroy()

    add_window = tk.Tk()
    add_window.title("Add New Words")
    add_window.geometry(f"{ADD_WINDOW_WIDTH}x{ADD_WINDOW_HEIGHT}")
    tk.Label(add_window, text="Prompts (one per line)").pack(pady=5)
    prompts_entry = tk.Text(add_window, height=15)
    prompts_entry.pack(pady=5)
    tk.Label(add_window, text="Answers (one per line)").pack(pady=5)
    answers_entry = tk.Text(add_window, height=15)
    answers_entry.pack(pady=5)
    tk.Button(add_window, text="Add", command=add_words).pack(pady=10)
    add_window.mainloop()

# Function to select a JSON file
def select_json_file():
    global data_file, data
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        data_file = file_path
        data = load_data(data_file)

# Main function to start the application
def main():
    global data
    data = load_data(data_file)

    main_window = tk.Tk()
    main_window.title("Language Study App")
    main_window.geometry("300x200")

    def start_study_session():
        study_thread = Thread(target=start_popup_timer)
        study_thread.start()

    def terminate_program():
        stop_event.set()
        main_window.destroy()

    tk.Button(main_window, text="Select JSON File", command=select_json_file).pack(pady=10)
    tk.Button(main_window, text="Add New Words", command=open_add_words_window).pack(pady=10)
    tk.Button(main_window, text="Start Study Session", command=start_study_session).pack(pady=10)
    tk.Button(main_window, text="Terminate", command=terminate_program).pack(pady=10)

    main_window.mainloop()

if __name__ == "__main__":
    main()
