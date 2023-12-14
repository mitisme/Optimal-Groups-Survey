import json
import smtplib
from flask import Flask, request, redirect, jsonify, session
from routes import routes
from routes import swaggerui_blueprint
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import time
import pandas as pd
import os
import csv
import traceback
import random
import string
import csvParser
import automate_email
import secrets
import models
parser = csvParser
emailer = automate_email


app = Flask(__name__, template_folder="frontend")
app.register_blueprint(routes)
app.register_blueprint(swaggerui_blueprint)
app.config['STORAGE_FOLDER'] = 'optimalgroups_csv_storage' 
app.config['NET_ID_IDENTIFIER'] = 'SIS Login ID'
app.config['COURSE_DATA_FILE'] = 'course_data.csv'
app.config['POSTFIX_IDS'] = '_Classlist.csv'
app.config['POSTFIX_PREFS'] = '_prefs.csv'
app.config['ABSOLUTE_PATH'] = os.path.join(os.path.expanduser("~"), "loop2/optimal-groups/ComS_402/")
#app.config['ABSOLUTE_PATH'] = ""
# MySQL credentials
with open(app.config['ABSOLUTE_PATH'] + 'config.json', 'r') as json_file:
    config_data = json.load(json_file)

mysql_host = config_data['mysql_host']
mysql_user = config_data['mysql_user']
mysql_password = config_data['mysql_password']
mysql_db = config_data['mysql_db']
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# connects SQLAlchemy instance to the Flask application
models.db.init_app(app)

# needed to prevent tampering of session data
app.config['SECRET_KEY'] = secrets.token_hex(16)

# needed to add this to execute the algorithm using the cron job 
# This may cause issues with local Testing
#app.config['ABSOLUTE_PATH'] = r'D:\\Homework\\COM S 402\\optimal-groups-copy\\optimal-groups\\ComS_402\\'
#app.config['ABSOLUTE_PATH'] = "" 

# Generates unique verification codes for the students in the class
def generate_codes(listLength, codeLength):
    codes = []
    random_string = ""
    characters = string.ascii_letters + string.digits  # Letters and numbers
    for x in range(listLength):
        random_string = ''.join(random.choice(characters) for _ in range(codeLength))
        while random_string in codes or random_string == "":
            random_string = ''.join(random.choice(characters) for _ in range(codeLength))
        codes.append(random_string)
    return codes

@app.route('/instructor-login', methods=['POST'])
def instructor_login():
    #get their netid
    data = request.get_json()
    netid = data.get('netid')
    #check if instructor is in database
    obj_instructor = (models.db.session.execute(models.db.select(models.Instructors.instructor_netid).filter_by(instructor_netid = netid)))
    instructor = obj_instructor.scalar()

    if instructor:
        # Access the code_expiration attribute of the instructor
        print(instructor)
        instructor = (models.db.session.execute(models.db.select(models.Instructors).filter_by(instructor_netid = netid))).scalar()
        id = instructor.instructor_id
        session['id'] = id
        print(id)
    else:
        return "Error, netid not found"

    return "finished"

@app.route("/instructor-delete/<netid>", methods=["DELETE"])
def delete_instructor(netid):   

    # Makes sure that request cannot be fulfilled through tools like Postman
    if "admin" not in session:
        return "admin"
    
    instructor = (models.db.session.execute(models.db.select(models.Instructors).filter_by(instructor_netid = netid))).scalar()
    if instructor and instructor.is_admin == 1:
        return "admin"
    
    elif instructor and instructor.is_admin == 0:
        course_data_ids = models.db.session.query(models.CourseData.course_data_id).filter_by(instructor_netid=netid).all()
        
        for (course_id,) in sorted(course_data_ids, key=lambda x: x[0]):
            # Delete rows in StudentPrefs where course_data_id=course_id
            print("deleting student prefs" + " for course_id: " + str(course_id))
            models.db.session.query(models.StudentPrefs).filter_by(course_data_id=course_id).delete()

            # Delete rows in CourseClasslists where course_data_id=course_id
            print("deleting classlists" + " for course_id: " + str(course_id))
            models.db.session.query(models.CourseClasslists).filter_by(course_data_id=course_id).delete()

            #Delete course data
            print("deleting course_data" + " for netid: " + netid)
            models.db.session.query(models.CourseData).filter_by(instructor_netid=netid).delete()
        
        #Delete instructor
        print("Instructor Deleted: " + netid)
        models.db.session.query(models.Instructors).filter_by(instructor_netid=netid).delete()
        # Commit the changes to the database
        models.db.session.commit()
        return "successful delete"

    else:
        return "not found"



@app.route("/get-instructors", methods=["GET"])
def send_instructors():
    instructor_details = models.db.session.query(models.Instructors.instructor_name, models.Instructors.instructor_netid).all()    # Convert list of tuples to list of strings
    
    instructor_list = [
    {'name': detail[0], 'netid': detail[1]}
    for detail in instructor_details
    ]
    # Serialize the list to a JSON array
    instructor_netids_json = {"instructors" : instructor_list}
    return jsonify(instructor_netids_json)


@app.route('/add-instructor', methods=['POST'])
def add_instructor():

    # Makes sure that request cannot be fulfilled through tools like Postman
    if 'admin' not in session:
        return 'fail'
    #get their netid from form
    #netid = 'mitisme'
    data = request.get_json()
    netid = data.get('netid')
    name = data.get('name')
    #generate a login code for them to use
    new_code = generate_codes(1, 7)[0]
    
    #set a deadline for the code
    current_time = datetime.now()
    expire_date = current_time + timedelta(hours=24)
    formatted_expire_date = expire_date.strftime("%Y-%m-%d %H:%M:%S.%f")

    #shouldnt be admin unless its the Client
    new_is_admin = False
    
    #set information for SQL
    insert_instructor_row = models.Instructors(
        instructor_name = name,
        instructor_netid = netid,
        verification_code = new_code,
        code_expiration = formatted_expire_date,
        is_admin = new_is_admin
    )
    try:
        models.db.session.add(insert_instructor_row)
        models.db.session.commit()

        #send email notification to new user
        emailer.send_invitation_email(name, netid, new_code, formatted_expire_date)
        return "success"
    except Exception as e:
        return "error"

# returns the email that received the authentication code
@app.route('/get-email', methods=['GET']) 
def get_email():
    id = session['id']
    instructor = (models.db.session.execute(models.db.select(models.Instructors).filter_by(instructor_id = id))).scalar()
    netid = instructor.instructor_netid
    email = f"{netid}@iastate.edu"

    return jsonify(email)

#Checks if the current stored authentication code is valid, if not send a new one
#returns "new_code" signalling we sent a brand new code
#returns "current_code" signalling to use the current code send less than 24 hours ago
@app.route('/send-code', methods=['GET']) 
def send_code():
    if 'id' not in session:
        return jsonify({"error": "Session 'id' not found"}), 401
    id = session['id']
    print(id)
    expiration = (models.db.session.execute(models.db.select(models.Instructors.code_expiration).filter_by(instructor_id = id))).scalar()
    #check if their code is expired
    current_time = datetime.now()
    expire_date = current_time + timedelta(hours=24)
    formatted_expire_date = expire_date.strftime("%Y-%m-%d %H:%M:%S.%f")

    print(expiration, formatted_expire_date)
    #code is expired send new one
    instructor = (models.db.session.execute(models.db.select(models.Instructors).filter_by(instructor_id = id))).scalar()
    if(current_time >= expiration):
        new_code = generate_codes(1, 7)[0]
        print("setting code: " + new_code)
        instructor.verification_code = new_code
        instructor.code_expiration = formatted_expire_date
        models.db.session.commit()
        emailer.send_verication_code(instructor.instructor_name,instructor.instructor_netid, new_code)
        print('sent new code: ' + str(new_code))
        return jsonify("new_code")
    else:
        print('using old code: '+ instructor.verification_code)
        return jsonify("current_code")

#This is a POST method used to check the code given by instructor to the code currently stored
#returns    expired -> new code was generated and sent to instructor
#returns    success -> code provided matched current code and proceed as normal
#return     fail    -> code provided didnt match current code, ask again for correct code
@app.route('/check-code', methods=['POST']) 
def check_code():

   
    try:
        id = session['id']
    except KeyError as e:
        app.logger.error(f"KeyError in /check-code: {e}. Session data: {session} id: {id}")
        raise Exception    
    data = request.get_json()
    check_code = data.get('codeInput') 
    expiration = (models.db.session.execute(models.db.select(models.Instructors.code_expiration).filter_by(instructor_id = id))).scalar()

    #check if their code is expired
    current_time = datetime.now()
    expire_date = current_time + timedelta(hours=24)
    formatted_expire_date = expire_date.strftime("%Y-%m-%d %H:%M:%S.%f")

    #code is expired send new one
    instructor = (models.db.session.execute(models.db.select(models.Instructors).filter_by(instructor_id = id))).scalar()
    if(current_time >= expiration):
        new_code = generate_codes(1, 7)[0]
        instructor.verification_code = new_code
        instructor.code_expiration = formatted_expire_date
        models.db.session.commit()
        print(instructor.instructor_netid)
        emailer.send_verication_code(instructor.instructor_name,instructor.instructor_netid, new_code)
        return "expired"
    
    elif(check_code == instructor.verification_code):
        isAdmin = models.db.session.execute(models.db.select(models.Instructors.is_admin).filter_by(instructor_id = id, is_admin = 1)).scalar()
        if isAdmin is not None:
            session['admin'] = True
        session["verified"] = True
        return "success", 200
    
    else:
        print("check_code fail", check_code )
        return "fail", 400
    

@app.route('/submit-form', methods=['POST'])
def upload_file():
    id = session['id']
    instructor_csv = request.files['file']
    form_group_size = request.form.get('groupSize') 
    deadlineDate = request.form.get('deadlineDate') 
    deadlineTime = request.form.get('deadlineTime')
    overallDeadline = deadlineDate + " " + deadlineTime
    form_course = request.form.get('course') or 'default_course'
    form_course = form_course.replace(" ", "_")
    # file_path = os.path.join(app.config['STORAGE_FOLDER'], secure_filename(
    #     form_course + '_Classlist.csv'))
    temp_csv = pd.read_csv(instructor_csv)
    instructor = (models.db.session.execute(models.db.select(models.Instructors).filter_by(instructor_id = id))).scalar()
    # Check if instructor has already uploaded a classlist for the course
    if models.db.session.execute(models.db.select(models.CourseData).filter_by(instructor_netid = instructor.instructor_netid, course_name = form_course)).scalar() is not None:
        return redirect('/frontend/errorDuplicateCourse.html')

    # add row to the course_data table
    insert_course_data_row = models.CourseData(
        # course_data_id not set here as it is auto incremented
        course_name = form_course,
        deadline = overallDeadline,
        group_size = form_group_size,
        instructor_netid = instructor.instructor_netid
    )
    models.db.session.add(insert_course_data_row)
    models.db.session.commit()

    # make DataFrame that includes the necessary columns from the uploaded csv
    new_classlist_df = pd.DataFrame()
    new_classlist_df['SIS Login ID'] = temp_csv[app.config['NET_ID_IDENTIFIER']]
    new_classlist_df['Student'] = temp_csv['Student']
    # add column for student verification code to take their unique survey
    new_classlist_df['Verification Code'] = generate_codes(len(temp_csv[app.config['NET_ID_IDENTIFIER']]), 8)

    # clean up the DataFrame
    cleaned_classlist_df = parser.clean_up(new_classlist_df)
    
    # needed values from the course_data row
    course_data_id_for_classlist = insert_course_data_row.course_data_id

    # add rows to the course_classlists table
    for index, row in cleaned_classlist_df.iterrows():
        insert_course_classlist_row = models.CourseClasslists(
            # classlist_id not set here as it is auto incremented
            course_data_id = course_data_id_for_classlist,
            student_netid  = row['SIS Login ID'],
            student_name = row['Student'],
            verification_code = row['Verification Code']
        )
        models.db.session.add(insert_course_classlist_row)
    models.db.session.commit()

    emailer.send_email_to_students(cleaned_classlist_df, course_data_id_for_classlist, form_course, overallDeadline)

    session.clear()
    return redirect('/frontend/success.html')

@app.route('/get-netids', methods=['GET'])
def get_netids():
    # Grab parameters from the URL
    studentCode = request.args.get('code')
    courseDataId = request.args.get('id') 

    # Making sure the url link includes both course name and verification code
    if studentCode == "null" or courseDataId == "null":
        return jsonify("invalid link"), 400
    
    # if the course instructor did not upload a classlist csv
    if models.db.session.execute(models.db.select(models.CourseClasslists.course_data_id).filter_by(course_data_id = courseDataId, verification_code = studentCode)).scalar() is None:
        return jsonify("This course does not use the Optimal Groups survey"), 400

    # Check if the student is in the uploaded classlist
    studentNetid = models.db.session.execute(models.db.select(models.CourseClasslists.student_netid).filter_by(course_data_id = courseDataId, verification_code = studentCode)).scalar()
    if studentNetid is None:
        return jsonify("Student is not in this class"), 400
    
    # Checks to see if the student's preferences have already been submitted
    recipientNetid = models.db.session.execute(models.db.select(models.StudentPrefs.student_netid).filter_by(course_data_id = courseDataId, student_netid = studentNetid)).scalar()
    if recipientNetid is not None:
        return jsonify("Survey has already been taken"), 400
    
    # grab deadline info from database
    temp = models.db.session.execute(models.db.select(models.CourseData.deadline).filter_by(course_data_id = courseDataId)).scalar()
    
    # Check to see if survey deadline has passed
    currentDate = datetime.now()
    surveyDeadline = datetime.strptime(temp, '%Y-%m-%d %H:%M')
    
    if currentDate > surveyDeadline:
        return jsonify("Deadline has passed"), 400    
    
    # name of the student who is going to take the survey
    removedName = models.db.session.execute(models.db.select(models.CourseClasslists.student_name).filter_by(verification_code = studentCode)).scalar()

    # query to get the rows of the student's classmates
    classmateRows = models.db.session.execute(models.db.select(models.CourseClasslists).filter(models.CourseClasslists.course_data_id == courseDataId, models.CourseClasslists.student_name != removedName)).scalars()
    classmateList = []
    for row in classmateRows :
        classmateList.append({"netid" : row.student_netid, "names" : row.student_name})
        
    dataDict = {"students": classmateList}
    jsonData = jsonify(dataDict)
    return jsonData

@app.route('/submit-survey', methods=['POST'])
def submit():
        data = request.get_json()
        # recipient's survey results
        survey_results = data.get('teammateList')
        courseDataId = data.get('course_data_id')
        recipient_code = data.get('code')
        courseName = models.db.session.execute(models.db.select(models.CourseData.course_name).filter_by(course_data_id = courseDataId)).scalar()

        # grab deadline info from database
        temp = models.db.session.execute(models.db.select(models.CourseData.deadline).filter_by(course_data_id = courseDataId)).scalar()
        currentDate = datetime.now()
        surveyDeadline = datetime.strptime(temp, '%Y-%m-%d %H:%M')
        
        if currentDate > surveyDeadline:
            return jsonify("Deadline has passed"), 400  
    
        # Ensures that a student won't retake the survey they already completed
        recipient_netid = models.db.session.execute(models.db.select(models.CourseClasslists.student_netid).filter_by(course_data_id = courseDataId, verification_code = recipient_code)).scalar()
        if models.db.session.execute(models.db.select(models.StudentPrefs.student_netid).filter_by(student_netid = recipient_netid, course_data_id = courseDataId)).scalar() is not None:
            return "Survey has already been taken", 400
        
        prefs_df = pd.DataFrame()

        teammates_data = []
        ranking_data =[]

        for teammate in survey_results:
            pref_rank = teammate[-1]
            teammates_data.append(teammate[:-1])

            if pref_rank == '1':
                pref_rank = '4'
            elif pref_rank == '2':
                pref_rank = '3'
            elif pref_rank == '3':
                pref_rank = '2'
            elif pref_rank == '4':
                pref_rank = '1'
            elif pref_rank == '5':
                pref_rank = '-10'
            elif pref_rank == '6':
                pref_rank = '-10'
        
            ranking_data.append(pref_rank)
        # Example prefs csv has no column headers so this one won't either
        # 0 -> Recipient, 1 -> Teammate Chosen, 3 -> Preference Points
        new_survey_data = pd.DataFrame({
            "RecipientStudent": [recipient_netid] * len(teammates_data),
            "PreferredTeammate": teammates_data,
            "PrefRanking": ranking_data
        })
        new_survey_data = new_survey_data.sort_values("PrefRanking", ascending=False)
        prefs_df = pd.concat([prefs_df, new_survey_data], ignore_index=True)

        for index, row in prefs_df.iterrows():
            insert_preference_row = models.StudentPrefs(
                # no need to include preference_id as it is auto-incremented
                course_data_id = courseDataId,
                course_name = courseName,
                student_netid = recipient_netid,
                preferred_student_netid = row['PreferredTeammate'],
                preferred_ranking = row['PrefRanking']
            )
            models.db.session.add(insert_preference_row)
        models.db.session.commit()
        
        return redirect('/frontend/thanks.html')

if __name__ == '__main__':
    app.run(debug=True)

