import json
import random
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta
from threading import Thread, Event

DEFAULT_DATA_FILE = 'language_data.json'
POPUP_INTERVAL = 30  # 0.5 minute
POPUP_WIDTH = 400
POPUP_HEIGHT = 200
POPUP_X = 1200  # Adjust based on screen resolution
POPUP_Y = 800   # Adjust based on screen resolution
ADD_WINDOW_WIDTH = 800
ADD_WINDOW_HEIGHT = 700
MAX_CONSECUTIVE_CORRECT = 5
NUMBER_OF_WORDS_PER_SESSION = 10

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

def update_last_checked_date(data):
    global last_checked_date
    current_date = datetime.now().date()
    if current_date != last_checked_date:
        last_checked_date = current_date

# Update the next test time based on performance
def schedule_next_test(word, response_time, correct):
    if 'results' not in word:
        word['results'] = ''

    # Update retention
    if correct:
        if word['results'] and word['results'][-1] == '+':
            last_successful_recall = datetime.strptime(word['last_successful_recall'], "%Y-%m-%dT%H:%M:%S.%f")
            retention_days = (datetime.now() - last_successful_recall).days
            word['retention_longest'] = max(word['retention_longest'], retention_days)
        word['last_successful_recall'] = datetime.now().isoformat()
    
    if correct:
        word['consecutive_correct'] += 1
        word['results'] += '+'
    else:
        word['consecutive_correct'] = 0
        word['results'] += '-'


    word['times_tested'] += 1
    word['accuracy_over_time'] = round(((word['accuracy_over_time'] * (word['times_tested'] - 1)) + (1 if correct else 0)) / word['times_tested'], 2)
    word['response_time'].append(round(response_time, 2))
    word['last_check_date'] = datetime.now().isoformat()

    # Adjust interval based on review frequency
    review_frequencies = {
        "30-Sec": timedelta(seconds=30),
        "Minutely": timedelta(minutes=1),
        "30-Min": timedelta(minutes=30),
        "Hourly": timedelta(hours=1),
        "Daily": timedelta(days=1),
        "3-Day": timedelta(days=3),
        "Weekly": timedelta(weeks=1),
        "2-Week": timedelta(weeks=2),
        "Monthly": timedelta(days=30)
    }
    next_interval = review_frequencies.get(word['review_frequency'], timedelta(minutes=1))

    word['next_possible_test_time'] = (datetime.now() + next_interval).isoformat()

# Check user input and update progress
def check_answer(word, user_input, response_time):
    correct = user_input.strip().lower() == word['answer'].strip().lower() or user_input.strip() == '.'
    word['lastest_response'] = user_input
    schedule_next_test(word, response_time, correct)
    return correct

# Show the popup
def show_popup(word):
    start_time = 0.0

    def on_space(event=None):
        nonlocal start_time
        start_time = time.time()  # Record the time when the user hits the spacebar
        prompt_label.config(text=word['prompt'])
        if word.get('example'):
            example_label.config(text=f"Example: {word['example']}")
        entry.focus()
        root.bind("<Return>", on_submit)  # Bind Enter key to submit

    def on_submit(event=None):
        response_time = time.time() - start_time  # Calculate the response time in seconds
        print(f"Response time: {response_time:.2f} seconds")
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

    prompt_label = tk.Label(root, text="Hit Spacebar...", wraplength=POPUP_WIDTH - 20)
    prompt_label.pack(pady=10)
    example_label = tk.Label(root, text="", wraplength=POPUP_WIDTH - 20, font=("Helvetica", 10, "italic"))
    example_label.pack(pady=5)

    entry = tk.Entry(root)
    entry.pack(pady=5)
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=5)
    result_label = tk.Label(root, text="")
    result_label.pack(pady=5)

    root.bind("<space>", on_space)  # Bind Spacebar to start the test
    root.mainloop()

# Trigger the popup at regular intervals
def start_popup_timer():
    while not stop_event.is_set():
        update_last_checked_date(data)
        now = datetime.now().isoformat()
        due_words = [word for word in data['words'] if word['next_possible_test_time'] <= now]
        if due_words:
            # Sort due_words by consecutive_correct and next_possible_test_time
            due_words.sort(key=lambda word: (word['next_possible_test_time'], word['consecutive_correct']))
            cutoff = len(due_words) // 2
            filtered_words = due_words[:cutoff]
            word = random.choice(filtered_words)
            show_popup(word)
        stop_event.wait(POPUP_INTERVAL)

# Interface to add new words and prompts
def add_word(prompt, answer, example=None):
    new_word = {
        "id": len(data['words']) + 1,
        "prompt": prompt,
        "example": example,
        "answer": answer,
        "lastest_response": '',
        "times_tested": 0,
        "consecutive_correct": 0,
        "results": '',
        "response_time": [],
        "response_time_trend": 'stable',
        "accuracy_over_time": 0,
        "accuracy_last_session": 0,
        "retention_longest": 0,         # number of days able to recall
        "retention_strength": "Weak",   # Weak, Moderate, Strong, Indestructible
        "retention_score": 0,
        "difficulty_score": 0,
        "difficulty_level": "Easy",     # low response time, high accuracy, high retention
        "review_frequency": "Minutely", # 30-Sec, Minutely, 30-Min, Hourly, Daily, 3-Day, Weekly, 2-Week, Monthly
        "last_check_date": datetime.now().isoformat(),          # last time the word was checked
        "last_successful_recall": datetime.now().isoformat(),   # last time the word was successfully recalled
        "next_possible_test_time": datetime.now().isoformat()
    }
    data['words'].append(new_word)
    save_data(data, data_file)

# Function to open the add words window
def open_add_words_window():
    def add_words():
        prompts = prompts_entry.get("1.0", tk.END).strip().split("\n")
        answers = answers_entry.get("1.0", tk.END).strip().split("\n")
        examples = examples_entry.get("1.0", tk.END).strip().split("\n")
        for prompt, answer, example in zip(prompts, answers, examples):
            add_word(prompt, answer, example)
        add_window.destroy()

    add_window = tk.Tk()
    add_window.title("Add New Words")
    add_window.geometry(f"{ADD_WINDOW_WIDTH}x{ADD_WINDOW_HEIGHT}")
    tk.Label(add_window, text="Prompts (one per line)").pack(pady=5)
    prompts_entry = tk.Text(add_window, height=10)
    prompts_entry.pack(pady=5)
    tk.Label(add_window, text="Answers (one per line)").pack(pady=5)
    answers_entry = tk.Text(add_window, height=10)
    answers_entry.pack(pady=5)
    tk.Label(add_window, text="Examples (one per line)").pack(pady=5)
    examples_entry = tk.Text(add_window, height=10)
    examples_entry.pack(pady=5)
    tk.Button(add_window, text="Add", command=add_words).pack(pady=10)
    add_window.mainloop()

# Function to select a JSON file
def select_json_file():
    global data_file, data, file_label
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        data_file = file_path
        data = load_data(data_file)
        file_label.config(text=f"Selected File: {file_path.split('/')[-1]}")

# Function to initialize a new JSON file
def init_json_file():
    global data_file, data
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        data_file = file_path
        data = {"words": [], "last_checked_date": datetime.now().isoformat()}
        save_data(data, data_file)

# Placeholder function for starting a cramming session
def start_cramming_session():
    pass

def start_study_session():
    global data
    # data = load_data(data_file)
    current_date = datetime.now().date()

    # Filter and sort words for the session
    due_words = [word for word in data['words'] if datetime.fromisoformat(word['next_possible_test_time']).date() <= current_date]
    due_words.sort(key=lambda word: datetime.fromisoformat(word['last_check_date']))
    reviewing_list = due_words[:NUMBER_OF_WORDS_PER_SESSION]
    review_required_list = []

    def check_word(word):
        show_popup(word)
        correct = word['results'][-1] == '+'
        
        # Log the result
        with open('session_log.txt', 'a') as log_file:
            log_file.write(f"{word['prompt']}, {datetime.now().isoformat()}, {word['lastest_response']}, {'Correct' if correct else 'Incorrect'}, {word['response_time'][-1]:.2f}, {word['review_frequency']}\n")
        
        # Update word and decide if it needs to be reviewed again
        if not correct or word['lastest_response'].strip().lower() == 'x':
            review_required_list.append(word)
        if word['consecutive_correct'] < 2:
            review_required_list.append(word)
        
        # Update next_possible_test_time
        if datetime.fromisoformat(word['next_possible_test_time']).date() > current_date:
            reviewing_list.remove(word)
        
        save_data(data, data_file)

    # Initial round
    for word in reviewing_list:
        check_word(word)
    
    # Queueing for the list
    while reviewing_list:
        word = reviewing_list.pop(0)
        while datetime.fromisoformat(word['next_possible_test_time']) <= datetime.now():
            check_word(word)
            break
        if word not in review_required_list:
            reviewing_list.append(word)
    
    # Export Review Required list
    with open('review_required_list.json', 'w') as review_file:
        json.dump([word['prompt'] for word in review_required_list], review_file)

# Main function to start the application
def main():
    global data, file_label
    data = load_data(data_file)

    main_window = tk.Tk()
    main_window.title("Language Study App by Brian")
    main_window.geometry("500x300")

    def start_study_session_thread():
        study_thread = Thread(target=start_study_session)
        study_thread.start()

    def terminate_program():
        stop_event.set()
        main_window.destroy()

    # Section for file operations and adding words
    file_ops_frame = tk.Frame(main_window)
    file_ops_frame.pack(pady=10)
    tk.Button(file_ops_frame, text="Select JSON File", command=select_json_file).pack(pady=5)
    tk.Button(file_ops_frame, text="Init JSON File", command=init_json_file).pack(pady=5)
    tk.Button(file_ops_frame, text="Add Words", command=open_add_words_window).pack(pady=5)
    file_label = tk.Label(file_ops_frame, text="")
    file_label.pack(pady=5)

    # Section for study and cramming sessions
    session_frame = tk.Frame(main_window)
    session_frame.pack(pady=10)
    tk.Button(session_frame, text="Start Chill Session", command=start_study_session_thread).pack(pady=5)
    tk.Button(session_frame, text="Start Intensive Session", command=start_cramming_session).pack(pady=5)

    # Section for termination
    tk.Button(main_window, text="Terminate", command=terminate_program).pack(pady=10)

    main_window.mainloop()

if __name__ == "__main__":
    main()
