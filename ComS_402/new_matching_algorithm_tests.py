import unittest
from unittest.mock import patch, MagicMock, mock_open
from new_matching_algorithm import convert_to_unix_timestamp, get_file_for_course, \
run_algorithm_for_courses, get_group, get_score, cost, count_no_positive_teammates, \
simulated_annealing, add_placeholders, random_swap, write_results_to_csv
from app import app
from flask import Flask
import datetime
from itertools import cycle


class NewMatchingAlgorithmTests(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    # Test convert_to_unix_timestamp with a valid test case
    def test_valid_date_time(self):
        date_test = "2023-01-01"
        time_test = "12:00"
        expected_timestamp = 1672596000 
        result = convert_to_unix_timestamp(date_test, time_test)
        self.assertEqual(result, expected_timestamp)

    # Test convert_to_unix_timestamp with an invalid test case
    def test_invalid_date_time(self):
        date_test = "invalid_string"
        time_test = "invalid_string"
        with self.assertRaises(ValueError):
            convert_to_unix_timestamp(date_test, time_test)
    
    # Test get_file_for_course for ids with a valid course
    @patch('models.CourseClasslists.query')
    @patch('models.CourseData')
    def test_get_ids_for_valid_course(self, mock_course_data, mock_classlists_query):
        mock_course_data.course_name = "ValidCourse"
        mock_classlists_query.join().filter().with_entities().all.return_value = [('student1',), ('student2',)]
        result = get_file_for_course("ValidCourse", "ids")
        self.assertEqual(result, ['student1', 'student2'])

    # Test get_file_for_course for ids with an invalid course
    @patch('models.CourseClasslists.query')
    @patch('models.CourseData')
    def test_get_ids_for_invalid_course(self, mock_course_data, mock_classlists_query):
        mock_course_data.course_name = "Invalid"
        mock_classlists_query.join().filter().with_entities().all.return_value = []
        result = get_file_for_course("Invalid", "ids")
        self.assertIsNone(result)

    # Test get_file_for_course for prefs with a valid course
    @patch('models.CourseClasslists.query')
    @patch('models.CourseData')
    def test_get_prefs_for_invalid_course(self, mock_course_data, mock_classlists_query):
        mock_course_data.course_name = "Invalid"
        mock_classlists_query.join().filter().with_entities().all.return_value = []
        result = get_file_for_course("Invalid", "prefs")
        self.assertEqual(result, {})
    
    # Test get_file_for_course for prefs with an invalid course
    @patch('new_matching_algorithm.StudentPrefs.query')
    @patch('new_matching_algorithm.CourseData')
    def test_get_prefs_for_valid_course(self, mock_course_data, mock_studentprefs_query):
        mock_course_data.course_name = "Valid Course"
        prefs_data = [
            ('student1', 'student2', 1),
            ('student2', 'student3', 2),
        ]
        mock_studentprefs_query.join().filter().with_entities().all.return_value = prefs_data
        result = get_file_for_course("Valid Course", "prefs")
        expected_result = {
            ('student1', 'student2'): 1,
            ('student2', 'student3'): 2,
        }
        self.assertEqual(result, expected_result)

    # Test that algorithm is being executed for courses when the deadline is past by mocking DB query result.
    # and mocking get_file_for_course function.
    @patch('new_matching_algorithm.CourseData.query')
    @patch('new_matching_algorithm.convert_to_unix_timestamp')
    @patch('new_matching_algorithm.get_file_for_course')
    @patch('new_matching_algorithm.simulated_annealing')
    @patch('new_matching_algorithm.emailer')
    def test_run_algorithm_for_courses_correct(self, mock_emailer, mock_simulated_annealing, mock_get_file_for_course, 
    mock_convert_to_unix_timestamp, mock_course_query):
        past_deadline = datetime.datetime.now() - datetime.timedelta(hours=1)
        mock_course = MagicMock()
        mock_course.course_name = "TestCourse"
        mock_course.deadline = past_deadline.strftime('%Y-%m-%d %H:%M')
        mock_course.group_size = 4
        mock_course.course_data_id = 1
        mock_course_query.all.return_value = [mock_course]
        mock_convert_to_unix_timestamp.return_value = past_deadline.timestamp()
        mock_get_file_for_course.return_value = ["data"] 
        run_algorithm_for_courses()
        mock_simulated_annealing.assert_called_once_with(["data"], ["data"], 4, "TestCourse")
        mock_emailer.send_email_to_instructor.assert_called_once_with(1)

    # Test that groups are being accurately picked according to number from the student assignments.
    def test_get_group(self):
        assignments = [('A', 1), ('B', 2), ('C', 1)]
        group_num = 1
        expected = ['A', 'C']
        self.assertEqual(get_group(assignments, group_num), expected)

    # Test that total preference scores are being accurately summed up when there are valid preferences.
    def test_get_score_for_group(self):
        group = ['A', 'B', 'C']
        prefs = {('A', 'B'): 1, ('B', 'A'): 2, ('B', 'C'): 3}
        self.assertEqual(get_score(group, prefs), 6)

    # Test that total preference scores are being accurately summed up when there are no valid preferences.
    def test_get_score_for_group_no_prefs(self):
        group = ['A', 'B', 'C']
        prefs = {}
        self.assertEqual(get_score(group, prefs), 0)

    # Test the cost function is accurate based on mocked get_score(results).
    @patch('new_matching_algorithm.get_score')
    def test_cost_function(self, mock_get_score):
        mock_get_score.side_effect = [10, 20, 30]  
        groups = [['group1'], ['group2'], ['group3']]
        prefs = {}  
        calculated_cost = cost(groups, prefs)
        expected_cost = -60 
        self.assertEqual(calculated_cost, expected_cost)
        self.assertEqual(mock_get_score.call_count, len(groups))
        for group in groups:
            mock_get_score.assert_any_call(group, prefs)

    # Test the count of teammates is accurate without preferences based on sample test case.
    def test_no_positive_teammates(self):
        prefs = {('A', 'B'): 2, ('D', 'A'): 2, ('C', 'D'): 1}
        groups = [['A', 'B'], ['C', 'D']]
        count = count_no_positive_teammates(groups, prefs)
        expected_count = 1
        self.assertEqual(count, expected_count)


    # Check that number of groups generated is accurate according to number of ids and preferred group size.
    # also ensures files are being generated
    @patch('new_matching_algorithm.cost')
    @patch('random.sample')
    @patch('random.choice')
    @patch('random.uniform')
    def test_no_of_groups_add_placeholders_even(self, mock_uniform, mock_choice, mock_sample, mock_cost):
        mock_uniform.return_value = 0  
        mock_cost.return_value = -8  
        mock_sample.return_value = [['A', 'B'], ['C', 'D']]
        mock_choice.return_value = 'A'
        ids = ['A', 'B', 'C', 'D']
        prefs = {('A', 'B'): 2, ('B', 'A'): 2, ('C', 'D'): 2, ('D', 'C'): 2}
        n = 2
        add_placeholders(n, ids, prefs)
        self.assertEqual(ids, ['A', 'B', 'C', 'D'])  
        self.assertEqual(prefs, {('A', 'B'): 2, ('B', 'A'): 2, ('C', 'D'): 2, ('D', 'C'): 2})  

    @patch('new_matching_algorithm.cost')
    @patch('random.sample')
    @patch('random.choice')
    @patch('random.uniform')
    # test other case were group size doesn't perfectly divide with no of students
    # also ensures files are being generated
    def test_no_of_groups_add_placeholders_uneven(self, mock_uniform, mock_choice, mock_sample, mock_cost):
        mock_uniform.return_value = 0  
        mock_cost.return_value = -8  
        mock_sample.return_value = [['A', 'B'], ['E', 'Placeholder1']]
        mock_choice.return_value = 'A'
        ids = ['A', 'B', 'C', 'D', 'E']
        n=4
        prefs = {}
        add_placeholders(n, ids, prefs)
        placeholders = [id for id in ids if "Placeholder" in id]
        self.assertEqual(len(placeholders), 3) 

    # Test that random swap correctly swaps members between groups
    def test_random_swap_success(self):
        group1 = ['A', 'B']
        group2 = ['C', 'D']
        member1 = 'A'
        member2 = 'C'
        result = random_swap(group1, group2, member1, member2)
        self.assertIn(member1, result[1])
        self.assertIn(member2, result[0])
    # Test that random does not  swaps members between groups when they're the same.
    def test_random_swap_failure(self):
        group1 = ['A', 'B']
        group2 = ['C', 'D']
        member1 = 'A'
        member2 = 'A'
        result = random_swap(group1, group2, member1, member2)
        self.assertIn(member1, result[0])
        self.assertIn(member2, result[0])

    # Test if write_to_csv writes the correct amount of rows and generates correct amount of files given the input.
    @patch('builtins.open', new_callable=mock_open)
    def test_write_results_to_csv(self, mock_file):
        course_name = 'TestCourse'
        best_score = 4
        best_score_2 = 2
        best_count = 0
        best_count_2 = 0
        best_table_score = [('A', 1), ('B', 2)]
        best_table_count = [('A', 2), ('B', 1)]
        write_results_to_csv(course_name, best_score, best_score_2, best_count, best_count_2, best_table_score, best_table_count)
        #test that 4 files are created.
        self.assertEqual(mock_file.call_count, 4)
        #check that writerow is being called correct amount of times.
        write_calls = sum(1 for call in mock_file.return_value.method_calls if call[0] == 'write')
        self.assertEqual(write_calls, 8)
    
    # Just test if it is reaching the point where it triggers results generation, as results have already been tested.
    @patch('new_matching_algorithm.write_results_to_csv') 
    def test_simulated_annealing_generates_results(self, mock_write_results_to_csv):
        ids = ['id1', 'id2', 'id3', 'id4']
        prefs = {('id1', 'id2'): 1, ('id2', 'id1'): 1, ('id3', 'id4'): 1, ('id4', 'id3'): 1}
        n = 2
        course_name = 'TestCourse'
        simulated_annealing(ids, prefs, n, course_name)
        mock_write_results_to_csv.assert_called()

if __name__ == '__main__':   
    unittest.main()  