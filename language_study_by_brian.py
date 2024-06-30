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

# Update the next test time
def schedule_next_test(word):
    word['times_tested'] += 1
    word['next_test_time'] = (datetime.now() + timedelta(minutes=POPUP_INTERVAL)).isoformat()

# Check user input and update progress
def check_answer(word, user_input):
    if user_input.strip().lower() == word['answer'].strip().lower():
        schedule_next_test(word)
        return True
    return False

# Show the popup
def show_popup(word):
    def on_submit():
        user_input = entry.get()
        if check_answer(word, user_input):
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
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=5)
    result_label = tk.Label(root, text="")
    result_label.pack(pady=5)
    root.mainloop()

# Trigger the popup at regular intervals
def start_popup_timer():
    while True:
        now = datetime.now().isoformat()
        due_words = [word for word in data['words'] if word['next_test_time'] <= now]
        if due_words:
            word = random.choice(due_words)
            show_popup(word)
        time.sleep(POPUP_INTERVAL)

# Interface to add new words and prompts
def add_word(prompt, answer):
    new_word = {
        "prompt": prompt,
        "answer": answer,
        "times_tested": 0,
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
