import json
from unittest import TestCase, mock
from unittest.mock import Mock
import pytest
from language_study_by_brian import load_data, save_data, reset_today_consecutive_correct, add_word
from datetime import datetime, timedelta

class TestLanguageStudyApp(TestCase):

    def test_load_data_nonexistent_file(self):
        """Test loading data from a non-existent file should return default data structure."""
        with mock.patch('builtins.open', mock.mock_open()) as mocked_file:
            mocked_file.side_effect = FileNotFoundError
            expected = {"words": [], "last_checked_date": datetime.now().date().isoformat()}
            result = load_data('nonexistent.json')
            self.assertEqual(result['words'], expected['words'])
            # Compare dates loosely due to possible second changes
            self.assertTrue(isinstance(result['last_checked_date'], str))

    def test_load_data_existing_file(self):
        """Test loading data from an existing file."""
        test_data = {"words": ["hello", "world"], "last_checked_date": "2022-01-01"}
        with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(test_data))) as mocked_file:
            with mock.patch('json.load', return_value=test_data):
                data = load_data('existent.json')
                self.assertEqual(data, test_data)

    def test_save_data(self):
        """Test saving data to a file."""
        test_data = {"words": ["hello", "world"], "last_checked_date": "2022-01-01"}
        with mock.patch('builtins.open', mock.mock_open()) as mocked_file:
            with mock.patch('json.dump') as mock_json_dump:
                save_data(test_data, 'somefile.json')
                mock_json_dump.assert_called_once_with(test_data, mock.ANY, indent=4)

    def test_reset_today_consecutive_correct_new_day(self):
        """Test resetting today's consecutive correct counts on a new day."""
        with mock.patch('language_study_by_brian.datetime') as mock_datetime:
            # Setup the mock to return a specific date when now() is called
            mock_datetime.now.return_value = datetime(2022, 1, 2)
            test_data = {'words': [{'today_consecutive_correct': 3}], 'last_checked_date': '2022-01-01'}
            reset_today_consecutive_correct(test_data)
            self.assertEqual(test_data['words'][0]['today_consecutive_correct'], 0)

    def test_reset_today_consecutive_correct_same_day(self):
        """Test not resetting today's consecutive correct counts on the same day."""
        current_date = datetime.now().date()
        test_data = {'words': [{'today_consecutive_correct': 3}], 'last_checked_date': current_date.isoformat()}
        reset_today_consecutive_correct(test_data)
        self.assertEqual(test_data['words'][0]['today_consecutive_correct'], 3)

    def test_add_word(self):
        """Test adding a new word to the data structure."""
        test_data = {'words': []}
        add_word(test_data, "hello", "world")
        self.assertIn({"prompt": "hello", "answer": "world", "consecutive_correct": 0}, test_data['words'])

@pytest.fixture
def app():
    """Fixture to handle global data setup if needed."""
    pass  # For future use if setup or teardown is needed

# To run the tests, use the command:
# pytest test_language_study.py
