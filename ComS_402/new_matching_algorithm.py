


import csv
import random
import math
from app import app
import os
import pandas as pd
import datetime
import automate_email
emailer = automate_email
from models import CourseData, CourseClasslists, StudentPrefs
'''
Run the simulated annealing function withs ids, prefs file and 
course name to generate CSVs that contain group matchings 
along with stats to measure performance.
'''

'''
This Simulated Annealing algorithm outperforms the original algorithm by a significant margin in terms of Total Preference
Scores across all group matchings, it also runs much faster (in less than 10 seconds) compared
to the original algorithm (30-40 seconds), and could still be optimized further in terms of time complexity.
'''

# want to test that when given a date string and a time conversion, the conversion is expected
def convert_to_unix_timestamp(date_str, time_str):
    return int(datetime.datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M').timestamp())

# want to test that the course ids and course prefs data is being properly retrieved
# since we can't query the db in a unit test, we will mock the results.
# also check invalid courses
def get_file_for_course(course, type):
    with app.app_context():
        if type == "ids":
            ids_query = CourseClasslists.query \
                .join(CourseData, CourseClasslists.course_data_id == CourseData.course_data_id) \
                .filter(CourseData.course_name == course) \
                .with_entities(CourseClasslists.student_netid) \
                .all()
            if ids_query:
                return [ids_tuple[0] for ids_tuple in ids_query]
            else:
                return None
        elif type == "prefs":
            prefs_query = StudentPrefs.query \
                .join(CourseData, StudentPrefs.course_data_id == CourseData.course_data_id) \
                .filter(CourseData.course_name == course) \
                .with_entities(StudentPrefs.student_netid, 
                        StudentPrefs.preferred_student_netid, 
                        StudentPrefs.preferred_ranking) \
                .all()
            if prefs_query:
                return {(prefs[0], prefs[1]): prefs[2] for prefs in prefs_query}
            else:
                return {}
            
# want to test that the function correctly triggers the algorithm when deadline is passed
# also check that it triggers the email module
# mock the behaviour of get_file_for_course and db queries
def run_algorithm_for_courses():
    with app.app_context():
        courses = CourseData.query.all()
        current_timestamp = datetime.datetime.now().timestamp()
        
        for course_data in courses:
            course_name = course_data.course_name   
            deadline = course_data.deadline

            group_size = course_data.group_size    
            deadline_timestamp = convert_to_unix_timestamp(deadline.split()[0], deadline.split()[1])

            if deadline_timestamp <= current_timestamp:
                if get_file_for_course(course_name, "ids") != None and get_file_for_course(course_name, "prefs") != None:
                    simulated_annealing(get_file_for_course(course_name, "ids"), get_file_for_course(course_name, "prefs"), group_size, course_name)
                    emailer.send_email_to_instructor(course_data.course_data_id)

def get_group(assign, num):
    return [item[0] for item in assign if item[1] == num]

def get_score(group, prefs):
    pref_score = 0
    for first in range(len(group)):
        for second in range(first+1, len(group)):
            if second != first:
              pref_score += prefs.get((group[first], group[second]), 0)
              pref_score += prefs.get((group[second], group[first]), 0)
    return pref_score

def cost(groups, prefs):
    return -sum([get_score(group, prefs) for group in groups])

# want to test that the student with prefs only takes positive prefs
# want to test that pref_count is accurate with mix of negative and positive prefs.
def count_no_positive_teammates(groups, prefs):
    count = 0
    students_with_prefs = [student for (student, student2), score in prefs.items() if score > 0]

    for group in groups:
        for student in group:
            pref_exists = False
            for teammate in group:
                if prefs.get((student, teammate), 0) > 0:
                    pref_exists = True
                    break
            if not pref_exists and student in students_with_prefs:
                count += 1
    return count

# want to test that no_of_groups is accurate, for both cases whether len(ids) % n > 0 or not.
def add_placeholders(n, ids, prefs):
    if len(ids) % n:
        num_of_placeholders = (n - (len(ids) % n))
    else:
        num_of_placeholders = 0
    for i in range(1, num_of_placeholders + 1):
        placeholder = f"Placeholder{i}"
        ids.append(placeholder)
        for id in ids:
            if id != placeholder and "Placeholder" in id:
                prefs[(id, placeholder)] = -1e9
                prefs[(placeholder, id)] = -1e9
    return ids, prefs

# want to test that members are being swapped
def random_swap(first_group, second_group, member1, member2):
    if member1 != member2:
        first_group.remove(member1)
        second_group.remove(member2)
        first_group.append(member2)
        second_group.append(member1)
    return first_group, second_group

# want to test that csv files are being created and right number of rows are written.
def write_results_to_csv(course_name, best_score, best_score_2, best_count, best_count_2, best_table_score, best_table_count):
    # Save best results and stats measuring performance to CSVs.
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_score.csv'), 'w', newline='') as groups_by_score:
        write = csv.writer(groups_by_score)
        for row in best_table_score:
            write.writerow(row)
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_score_stats.csv'), 'w', newline='') as score_stats:
        write = csv.writer(score_stats)
        write.writerow(["Total Preference Score", "No of Students without preferred teammates"])
        write.writerow([best_score, best_count_2])
    print(f"Best Solution (optimized on pref scores): {best_score}")
    print(f"Number of students without a preferred teammate: {best_count_2}")
    for row in best_table_score:
        first, second = row
        print(str(first) + ", " + str(second))
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_prefs.csv'), 'w', newline='') as groups_by_prefs:
        write = csv.writer(groups_by_prefs)
        for row in best_table_count:
            write.writerow(row)
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_prefs_stats.csv'), 'w', newline='') as prefs_stats:
        write = csv.writer(prefs_stats)
        write.writerow(["Total Preference Score", "No of Students without preferred teammates"])
        write.writerow([best_score_2, best_count])
    print(f"Best Solution (optimized on no. of students who didn't get their preferences): {best_score}")
    print(f"Number of students without a preferred teammate: {best_count}")
    for row in best_table_count:
        first, second = row
        print(str(first) + ", " + str(second))


def simulated_annealing(ids, prefs, n, course_name, experiment_runs=25):

    best_score = float('-inf')
    best_score_2 = float('-inf')
    best_count = float('inf')
    best_count_2 = float('inf')
    best_table_score = None
    best_table_count = None
    ids, prefs = add_placeholders(n, ids, prefs)
    no_of_groups = len(ids) // n
    for _ in range(experiment_runs):
        curr = []
        for id in range(0, len(ids), n):
          group = ids[id:id+n]
          curr.append(group)
        current_cost = cost(curr, prefs)
        # set an init temperature
        initial_temp = 1000
        # set a cooling rate based on which it would accept "bad" solutions
        cooling_rate = 0.995 + random.uniform(-0.005, 0.005)
        # cap the number of iterations
        iterations = 10000
        temperature = initial_temp

        for _ in range(iterations):
            sol = [group.copy() for group in curr]
            first_group, second_group = random.sample(sol, 2)
            member1, member2 = random.choice(first_group), random.choice(second_group)
            # randomly swap group members between 2 diff groups. 
            first_group, second_group = random_swap(first_group, second_group, member1, member2)
            new_cost = cost(sol, prefs)
            # accept suboptimal solutions with some probabbility e^(cost_diff) / t
            if new_cost < current_cost or random.random() < math.exp((current_cost - new_cost) / temperature):
                curr, current_cost = sol, new_cost
            # decrease temperature according to cooling rate after each iteration    
            temperature *= cooling_rate
        results = []
        for group_number, group in enumerate(curr, 1):
             for net_id in group:
                results.append((net_id, group_number))
        score = -current_cost

        sa_groups = []
        for group_num in range(1, int(no_of_groups) + 1):
            group = get_group(results, group_num)
            sa_groups.append(group)

        count_sa = count_no_positive_teammates(sa_groups, prefs)
        # Save the group assingments with max preference score so far.
        if score > best_score or (score == best_score and count_sa < best_count_2):
            best_score = score
            best_count_2 = count_sa
            best_table_score = results
        # Save the group assignments with least number of students who didn't get their prefs so far.
        if count_sa < best_count or (count_sa == best_count and score > best_score_2):
            best_score_2 = score
            best_count = count_sa
            best_table_count = results
    write_results_to_csv(course_name, best_score, best_score_2, best_count, best_count_2, best_table_score, best_table_count)


if __name__ == "__main__":
    run_algorithm_for_courses()







