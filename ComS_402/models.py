from flask_sqlalchemy import SQLAlchemy

# initialize instance of SQLAlchemy
db = SQLAlchemy()

# the following classes represent the tables in the MySQL database
class Instructors (db.Model):
    __tablename__ = 'instructors'
    instructor_name = db.Column('instructor_name',db.String(100))
    instructor_id = db.Column('instructor_id', db.Integer, autoincrement = True, primary_key=True)
    instructor_netid = db.Column('instructor_netid', db.String(300), unique=True)
    verification_code = db.Column('verification_code', db.String(7))
    code_expiration = db.Column('code_expiration', db.DATETIME)
    is_admin = db.Column('is_admin', db.Boolean)

class CourseData (db.Model):
    __tablename__ = 'course_data'

    course_data_id = db.Column('course_data_id', db.Integer, autoincrement = True, primary_key = True)
    course_name = db.Column('course_name', db.String(300))
    deadline = db.Column('deadline', db.String(300))
    group_size = db.Column('group_size', db.Integer)
    instructor_netid = db.Column('instructor_netid', db.String(300), db.ForeignKey('instructors.instructor_netid'))

    __tableargs__ = (db.UniqueConstraint('instructor_netid', 'course_name'))

class CourseClasslists (db.Model):
    __tablename__ = 'course_classlists'

    classlist_id = db.Column('classlist_id', db.Integer, autoincrement = True, primary_key = True)
    course_data_id = db.Column('course_data_id', db.Integer, db.ForeignKey('course_data.course_data_id'))
    student_netid = db.Column('student_netid', db.String(100))
    student_name = db.Column('student_name', db.String(100))
    verification_code = db.Column('verification_code', db.String(8))

class StudentPrefs (db.Model):
    __tablename__ = 'student_prefs'

    preference_id = db.Column('preference_id', db.Integer, autoincrement = True, primary_key = True)
    course_data_id = db.Column('course_data_id', db.Integer, db.ForeignKey('course_data.course_data_id'))
    course_name = db.Column('course_name', db.String(300))
    student_netid = db.Column('student_netid', db.String(300))
    preferred_student_netid = db.Column('preferred_student_netid', db.String(300))
    preferred_ranking = db.Column('preferred_ranking', db.Integer)
