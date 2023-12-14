This directory is solely for Algorithm performance testing cross verification purposes.

The tests are run on different variatons of the student preferences files (named as variant_1, variant_2, .... and so on.)

These preference files simulate varying student preferences selected by the students in a class of 40+ students.

For the new algorithm, only the best out of the 25 results is picked. 

The best 2 results are picked based on the results which perform the best on 1. Preference Scores, 2. No of unsatisfied students, therefore in some cases both these results could be the same.

To run the test on different variants of the student prefs data"

**For the Old Algorithm: Change Line #19 froms prefs.csv in old_algorithm.py to any one of the variant_.csv files in this module.**

**For the New Algorithm:
Change Line #154 froms prefs.csv in new_algorithm.py to any one of the variant_.csv files in this module.**


To run the Old Algorithm, execute
python3 run_old_algorithm_tests.py

To run the New Algorithm, execute
python3 run_new_algorithm_tests.py

This will show you the time taken for each run of the algorithm, as well as preference score
and unsatisfied student stats for each algorithm.



