###Data Storage:

* Use a JSON file to store the list of words/prompts and progress.
* JSON structure:
```json
{
  "words": [
    {
      "prompt": "prompt text",
      "answer": "correct answer",
      "times_tested": 0,
      "next_test_time": "timestamp"
    },
    ...
  ]
}
```

###Main Application Logic:

* Initialize the application and load data from JSON.
* Set up a timer to trigger a popup every 5 minutes.
* Display a random prompt in the popup.
* Accept user input and compare it with the correct answer.
* Update the progress and reschedule the next test time.
* Save the updated progress back to the JSON file.

###opup UI:

* Use tkinter for creating a simple GUI popup.
* Display the prompt and a textbox for user input.

###Functionality to Add New Words:

* Provide a separate interface for adding new words/prompts.
* Update the JSON file with the new entries.