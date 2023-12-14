CREATE DATABASE IF NOT EXISTS optimal_groups_db;

CREATE TABLE IF NOT EXISTS optimal_groups_db.instructors (
    instructor_id INT AUTO_INCREMENT PRIMARY KEY,
    instructor_name VARCHAR(100),
    instructor_netid VARCHAR(300) UNIQUE NOT NULL,
    verification_code VARCHAR(7),
    code_expiration DATETIME,
    is_admin BOOLEAN
);

CREATE TABLE IF NOT EXISTS optimal_groups_db.course_data (
	course_data_id int auto_increment PRIMARY KEY,
	course_name varchar(300),
    deadline varchar(300),
    group_size int,
    instructor_netid varchar(300),
    UNIQUE(instructor_netid, course_name), -- makes sure that an instructor doesn't have multiple classlists of a course
    FOREIGN KEY (instructor_netid) references optimal_groups_db.instructors(instructor_netid)
);

 CREATE TABLE IF NOT EXISTS optimal_groups_db.course_classlists (
	 classlist_id int auto_increment PRIMARY KEY, -- needed to allow multiple instructors to submit their own classlist if there are other instructors that teach the same course
     course_data_id int,
	 student_netid varchar(100),
	 student_name varchar(100),
	 verification_code varchar(8),
     FOREIGN KEY (course_data_id) references optimal_groups_db.course_data(course_data_id)
 );
 
 CREATE TABLE IF NOT EXISTS optimal_groups_db.student_prefs (
	preference_id int auto_increment PRIMARY KEY,
    course_data_id int,
	course_name varchar(300),
    student_netid varchar(300),
    preferred_student_netid varchar(300),
    preferred_ranking int,
    FOREIGN KEY (course_data_id) references optimal_groups_db.course_data(course_data_id)
    );
   
INSERT INTO optimal_groups_db.instructors (instructor_name, instructor_netid, verification_code, code_expiration, is_admin)
VALUES ('Scott Johnson', 'sgj68', '1234567', '2023-12-10 08:00:00', 1) as restart_admin
ON DUPLICATE KEY UPDATE
  instructor_name = restart_admin.instructor_name,
  verification_code = restart_admin.verification_code,
  code_expiration = restart_admin.code_expiration,
  is_admin = restart_admin.is_admin
  ;