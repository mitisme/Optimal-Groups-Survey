import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from email.mime.application import MIMEApplication
from datetime import datetime
import app
import pandas as pd
import csv
import json
import os
from flask import session


ABSOLUTE_PATH = os.path.join(os.path.expanduser("~"), "loop2/optimal-groups/ComS_402/")

#ABSOLUTE_PATH = ""
def create_email_csv_file(file_path, result1, result2, data1, data2):
    result1 = result1[result1['Student Name'].str.contains('Placeholder') == False].reset_index(drop=True)
    result2 = result2[result2['Student Name'].str.contains('Placeholder') == False].reset_index(drop=True)
    data = [
        ["Result 1", "", "", "", "", "", "", "Result 2", "", "", "", "", ""],
        ["", "Name", "Group", "Pref Score", "Unsatisfied", "", "", "", "Name", "Group", "Pref Score", "Unsatisfied", ""],
        ["",result1['Student Name'][0], result1['Result'][0], str(data1._get_value(0, "Total Preference Score")), str(data1._get_value(0, "No of Students without preferred teammates")), "", "", "", result2['Student Name'][0], result2['Result'][0], str(data2._get_value(0, "Total Preference Score")), str(data2._get_value(0, "No of Students without preferred teammates")), ""]
        # ["Name2", "1", "", "", "", "", "", "Name2", "1", "", "", "", ""],
        # ["Name3", "1", "", "", "", "", "", "Name3", "1", "", "", "", ""],
        # ["", "Name4", "1", "", "", "", "", "", "Name4", "1", "", "", "", ""]
    ]
    for i in range(1, len(result1)):
        data.append(["",result1['Student Name'][i], result1['Result'][i], "", "", "", "", "", result2['Student Name'][i], result1['Result'][i]])

    with open(file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(data)

def send_verication_code(name, netid, code):
    # Open and read the JSON file
    with open(ABSOLUTE_PATH+ 'config.json', 'r') as json_file:
        config_data = json.load(json_file)

    # Access the values of "email" and "instructor" keys
    sender_email = config_data['email']
    instructor_email = f"{netid}@iastate.edu"
    server = smtplib.SMTP('Mailhub.iastate.edu', 587)
    server.connect("Mailhub.iastate.edu", 587)
    server.starttls()
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = instructor_email
    subject = 'Optimal Groups Survey'
    msg['Subject'] = subject
    html_content = f"""
<html>
<head></head>
<body>
<p style="font-family: Arial, sans-serif; font-size: 14px;">Hello {name}!</p>
<table style="margin-left: 20px; font-family: Arial, sans-serif; font-size: 14px;">
    <tr>
        <td>
            Please enter the following code below into the Optimal Groups's web application to continue:
        </td>
    </tr>
    <tr>
        <td style="padding-left: 40px;">
            <b style="font-size: 18px;">Code: {code}</b>
        </td>
    </tr>
</table>
<p style="font-family: Arial, sans-serif; font-size: 14px;">This code is valid for the next 24 hours.</p>
<p style="font-family: Arial, sans-serif; font-size: 14px;">If you did not try to access the Optimal Groups web application, you may want to contact Iowa State's IT or Computer Services.</p>
<p style="font-family: Arial, sans-serif; font-size: 14px;">Thanks for using Optimal Groups Survey!</p>
</body>
</html>
"""
# Create an email message
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_content, 'html'))
    text = msg.as_string()

    # Send the email
     # Send the email
    try:
        server.sendmail(sender_email, instructor_email, text)
        print("Sent to: " + instructor_email)
    except smtplib.SMTPRecipientsRefused as e:
        # Handle recipient refused exception
        print(f"Recipient {instructor_email} is invalid. Skipping.")
    except smtplib.SMTPException as e:
        # Handle SMTP-related exceptions (e.g., connection issues, email format errors)
        print(f"SMTP Exception: {e}")

    except FileNotFoundError as e:
        # Handle file-related exceptions (e.g., config.json or class CSV file not found)
        print(f"File Not Found Exception: {e}")

    except Exception as e:
        # Handle other unexpected exceptions
        print(f"An error occurred: {e}")

    finally:
        # Close the email server
        server.quit()

    return False

def send_invitation_email(name, netid, new_code, formatted_expire_date):
    with open('config.json', 'r') as json_file:
        config_data = json.load(json_file)

        # Access the values of "email" and "instructor" keys
    sender_email = config_data['email']

    #make the date more readable
    date_time_obj = datetime.strptime(formatted_expire_date, "%Y-%m-%d %H:%M:%S.%f")
    formatted_date_time = date_time_obj.strftime('%B %d, %Y, %I:%M %p')

    #server = smtplib.SMTP('smtp.gmail.com', 587) #keep for gmail please
    server = smtplib.SMTP('Mailhub.iastate.edu', 587)
    server.connect('Mailhub.iastate.edu')
    server.starttls()
    email = f"{netid}@iastate.edu"
    link = f'http://{config_data["server_domain"]}/frontend/instructorNetid.html'    
    #link = f'http://127.0.0.1:5000/frontend/instructorNetid.html'
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    subject = 'Optimal Groups Survey Invitation'
    msg['Subject'] = subject
    email_body = f"""Hello {name}! You've been given access to the Optimal Groups Survey! You can now log into our web application found at: {link}
        
Once you've accessed the link, enter your netid, then type in the following code for authentication:
        
Verification code: {new_code}
        
This code will be valid until {formatted_date_time}. After this time has passed, a new code will be sent the next time you log in.
A connection to Iowa State University's Wi-Fi will be required. You can use the following VPN for remote access:
https://it.engineering.iastate.edu/how-to/install-and-connect-to-vpn-pc/
        
For any additional information or questions, please contact Iowa State University's IT department or Dr. Scott Johnson.
Thanks for using the Optimal Groups Survey!"""

    msg.attach(MIMEText(email_body, 'plain'))
    text = msg.as_string()

    # Send the email
    try:
        server.sendmail(sender_email, email, text)
        print("Sent to: " + email)
    except smtplib.SMTPRecipientsRefused as e:
        # Handle recipient refused exception
        print(f"Recipient {email} is invalid. Skipping.")
    except smtplib.SMTPException as e:
        # Handle SMTP-related exceptions (e.g., connection issues, email format errors)
        print(f"SMTP Exception: {e}")

    except FileNotFoundError as e:
        # Handle file-related exceptions (e.g., config.json or class CSV file not found)
        print(f"File Not Found Exception: {e}")

    except Exception as e:
        # Handle other unexpected exceptions
        print(f"An error occurred: {e}")

    finally:
        # Close the email server
        server.quit()


def send_email_to_students(class_df, course_data_id, course, deadline):
    try:

        # Parse the deadline into a more readable form
        date_time_obj = datetime.strptime(deadline, '%Y-%m-%d %H:%M')
        formatted_date_time = date_time_obj.strftime('%B %d, %Y, %I:%M %p')
        # Initialize email content
        # Open and read the JSON file
        with open(ABSOLUTE_PATH + 'config.json', 'r') as json_file:
            config_data = json.load(json_file)

        # Access the values of "email" and "instructor" keys
        sender_email = config_data['email']

        #server = smtplib.SMTP('smtp.gmail.com', 587) #keep for gmail please
        server = smtplib.SMTP('Mailhub.iastate.edu', 587)
        server.connect('Mailhub.iastate.edu')
        server.starttls()
    
        for index, row in class_df.iterrows():
            if len(row) >= 3:
                netid = row['SIS Login ID']
                name = row['Student']
                code = row['Verification Code']
                email = f"{netid}@iastate.edu"
                link = f'http://{config_data["server_domain"]}/frontend/preferences.html?id={course_data_id}&code={code}'
                #link = f'http://127.0.0.1:5000/frontend/preferences.html?id={course_data_id}&code={code}'
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = email
                subject = course + ': ' + 'Optimal Groups Survey'
                msg['Subject'] = subject
                email_body = f"""Hello {name},

    Your {course} instructor has assigned you this Optimal Groups survey. This is a survey designed to optimize groups based on students' preferences.

    To complete the survey, please click on the following link: {link}

    The deadline for this survey is set for {formatted_date_time}. We ask that you submit your responses before this date to ensure the best overall group creation.

    Please note that to access the survey, you will need to be connected to the campus Wi-Fi. If you are not on campus, you can connect via the ISU VPN by following these instructions: https://it.engineering.iastate.edu/how-to/install-and-connect-to-vpn-pc/.

    Your participation in this survey is greatly appreciated.

    If you have any questions or encounter any issues while completing the survey.

    (This is an automated email, responses or emails sent to this email address will not be received or answered)

    Best regards,

    Optimal Groups Survey Team
    """

                msg.attach(MIMEText(email_body, 'plain'))
                text = msg.as_string()

                # Send the email
                try:
                    server.sendmail(sender_email, email, text)
                    print("Sent to: " + email)
                except smtplib.SMTPRecipientsRefused as e:
                    # Handle recipient refused exception
                    print(f"Recipient {email} is invalid. Skipping.")
    except smtplib.SMTPException as e:
        # Handle SMTP-related exceptions (e.g., connection issues, email format errors)
        print(f"SMTP Exception: {e}")

    except FileNotFoundError as e:
        # Handle file-related exceptions (e.g., config.json or class CSV file not found)
        print(f"File Not Found Exception: {e}")

    except Exception as e:
        # Handle other unexpected exceptions
        print(f"An error occurred: {e}")

def send_email_to_instructor(courseDataId): #USE THIS EMAIL FOR FINAL PRODUCT: sgj68@iastate.edu
    # Open and read the JSON file
    with open(ABSOLUTE_PATH + 'config.json', 'r') as json_file:
        config_data = json.load(json_file)

    # Access the values of "email" and "instructor" keys
    sender_email = config_data['email']
    
    class_name = (app.models.db.session.execute(app.models.db.select(app.models.CourseData.course_name).filter_by(course_data_id = courseDataId))).scalar()
    instructor_netid = (app.models.db.session.execute(app.models.db.select(app.models.CourseData.instructor_netid).filter_by(course_data_id = courseDataId))).scalar()
    netid = instructor_netid
    email = f"{netid}@iastate.edu"
    #server = smtplib.SMTP('smtp.gmail.com', 587) #keep this for gmail testing please
    server = smtplib.SMTP('Mailhub.iastate.edu', 587)
    server.connect('Mailhub.iastate.edu')
    server.starttls()
    #server.login(sender_email, config_data['sender_password'])
    # Open the CSV file and create dataframes for reading statistics
    prefs_stats_file_path = os.path.join(ABSOLUTE_PATH + 'optimalgroups_csv_storage', secure_filename(class_name + '_best_by_prefs_stats.csv'))
    prefs_stats_df = pd.read_csv(prefs_stats_file_path)

    score_stats_file_path = os.path.join(ABSOLUTE_PATH + 'optimalgroups_csv_storage', secure_filename(class_name + '_best_by_score_stats.csv'))
    score_stats_df = pd.read_csv(score_stats_file_path)

    prefs_file_path = os.path.join(ABSOLUTE_PATH + 'optimalgroups_csv_storage', secure_filename(class_name + '_best_by_prefs.csv'))
    prefs_df = pd.read_csv(prefs_file_path)

    score_file_path = os.path.join(ABSOLUTE_PATH + 'optimalgroups_csv_storage', secure_filename(class_name + '_best_by_score.csv'))
    score_df = pd.read_csv(score_file_path)

    # Open the class CSV file for sending emails

    

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    subject = class_name + ': ' + 'Optimal Groups Results'
    msg['Subject'] = subject
    email_body = f"""Hello, this is an automated email from the Optimal Groups Survey!

Here are the results from the surveys:

Thanks for using Optimal-Groups-Survey!
    """

    first_prefs_values = list(prefs_df.keys())
    pref_with_students = {'Student Name': prefs_df.iloc[:, 0], 'Result': prefs_df.iloc[:, 1]}
    pref_student_df = pd.DataFrame(pref_with_students)
    first_pref_data = pd.Series({'Student Name': first_prefs_values[0], 'Result': first_prefs_values[1]})
    pref_student_df = pd.concat([first_pref_data.to_frame().T, pref_student_df], ignore_index=True)
    print(pref_student_df)
    
    first_score_values = list(score_df.keys())
    score_with_students = {'Student Name': score_df.iloc[:, 0], 'Result': score_df.iloc[:, 1]}
    score_student_df = pd.DataFrame(score_with_students)
    first_score_data = pd.Series({'Student Name': first_score_values[0], 'Result': first_score_values[1]})
    score_student_df = pd.concat([first_score_data.to_frame().T, score_student_df], ignore_index=True)
    print(score_student_df)

    data_file_path = os.path.join(ABSOLUTE_PATH + 'optimalgroups_csv_storage', secure_filename(class_name + "_data.csv"))
    create_email_csv_file(data_file_path, pref_student_df, score_student_df, prefs_stats_df, score_stats_df)
    
    # Attach the .csv file to the email
    with open(data_file_path, 'rb') as file1:
        attachment1 = MIMEApplication(file1.read())
        attachment1.add_header('Content-Disposition', 'attachment', filename=class_name + '_OPTIMAL_GROUPS.csv')
        msg.attach(attachment1)

    msg.attach(MIMEText(email_body, 'plain'))
    text = msg.as_string()

    # Send the email
    server.sendmail(sender_email, email, text)

    removed_course_data_id = courseDataId
    print(netid)
 
    # Delete rows in StudentPrefs where course_data_id=removed_course_data_id
    print("deleting student prefs" + " for course_id: " + str(removed_course_data_id))
    app.models.db.session.query(app.models.StudentPrefs).filter_by(course_data_id=removed_course_data_id).delete()

    # Delete rows in CourseClasslists where course_data_id=removed_course_data_id
    print("deleting classlists" + " for course_id: " + str(removed_course_data_id))
    app.models.db.session.query(app.models.CourseClasslists).filter_by(course_data_id=removed_course_data_id).delete()

    #Delete course data
    print("deleting course_data" + " for netid: " + netid)
    app.models.db.session.query(app.models.CourseData).filter_by(course_data_id=removed_course_data_id).delete()

    app.models.db.session.commit()

    #delete temp files
    os.remove(prefs_stats_file_path)
    os.remove(score_stats_file_path)
    os.remove(prefs_file_path)
    os.remove(score_file_path)
    os.remove(data_file_path)

    # Close the email server
    server.quit()
    return False

# Call the send_email function with your CSV file paths
if __name__ == '__main__':
    send_email_to_instructor("COMS_402")
    #send_verication_code()
    print("")