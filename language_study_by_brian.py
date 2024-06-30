import json
import random
import time
import tkinter as tk
from datetime import datetime, timedelta
from threading import Timer

DATA_FILE = 'language_data.json'
POPUP_INTERVAL = 300  # 5 minutes

# Load data from JSON file
def load_data():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"words": []}

# Save data to JSON file
def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Update the next test time based on performance
def schedule_next_test(word, response_time, correct):
    if correct:
        word['consecutive_correct'] += 1
    else:
        word['consecutive_correct'] = 0

    word['times_tested'] += 1

    # Adjust interval based on performance
    if word['consecutive_correct'] >= 3:
        next_interval = timedelta(minutes=POPUP_INTERVAL * 4)
    elif word['consecutive_correct'] == 2:
        next_interval = timedelta(minutes=POPUP_INTERVAL * 2)
    elif response_time < 5:
        next_interval = timedelta(minutes=POPUP_INTERVAL * 1.5)
    else:
        next_interval = timedelta(minutes=POPUP_INTERVAL)

    word['next_test_time'] = (datetime.now() + next_interval).isoformat()

# Check user input and update progress
def check_answer(word, user_input, response_time):
    correct = user_input.strip().lower() == word['answer'].strip().lower()
    schedule_next_test(word, response_time, correct)
    return correct

# Show the popup
def show_popup(word):
    start_time = time.time()

    def on_submit():
        response_time = time.time() - start_time
        user_input = entry.get()
        if check_answer(word, user_input, response_time):
            result_label.config(text="Correct!")
        else:
            result_label.config(text="Try again!")
        save_data(data)
        root.after(2000, root.destroy)  # Close after 2 seconds

    root = tk.Tk()
    root.title("Language Study")
    root.geometry("300x150")
    prompt_label = tk.Label(root, text=word['prompt'])
    prompt_label.pack(pady=10)
    entry = tk.Entry(root)
    entry.pack(pady=5)
    submit_button = tk.Button(root, text="Submit", command(on_submit))
    submit_button.pack(pady=5)
    result_label = tk.Label(root, text="")
    result_label.pack(pady=5)
    root.mainloop()

# Trigger the popup at regular intervals
def start_popup_timer():
    while True:
        now = datetime.now().isoformat()
        due_words = [word for word in data['words'] if word['next_test_time'] <= now]
        for word in due_words:
            show_popup(word)
        time.sleep(POPUP_INTERVAL)

# Interface to add new words and prompts
def add_word(prompt, answer):
    new_word = {
        "prompt": prompt,
        "answer": answer,
        "times_tested": 0,
        "consecutive_correct": 0,
        "next_test_time": datetime.now().isoformat()
    }
    data['words'].append(new_word)
    save_data(data)

# Main function
if __name__ == "__main__":
    data = load_data()
    
    # Example to add a new word
    add_word("Hello", "こんにちは")
    
    # Start the popup timer
    popup_timer = Timer(POPUP_INTERVAL, start_popup_timer)
    popup_timer.start()
