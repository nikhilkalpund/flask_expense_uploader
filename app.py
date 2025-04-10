from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
import os
from werkzeug.utils import secure_filename
from email.message import EmailMessage
import smtplib

app = Flask(__name__, static_folder='uploads')
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

submissions = []


def send_email_notification(name, account_no, ifsc, details):
    msg = EmailMessage()
    msg['Subject'] = f'New Expense Submission from {name}'
    msg['From'] = 'nikhilkalpund@gmail.com'  # Replace with your sender email

    # List of admin email recipients
    recipients = ['kalpundajeet@gmail.com', 'nikhilkalpund@gmail.com']
    msg['To'] = ', '.join(recipients)

    msg.set_content(f'''
A new expense has been submitted:

Name: {name}
Account Number: {account_no}
IFSC Code: {ifsc}
Details: {details}

Check the admin panel for more information.
    ''')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('nikhilkalpund@gmail.com',
                       'pauz qyek jecb iauy')  # Replace with your app password
            smtp.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print("Email failed:", e)


@app.route('/', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'POST':
        expense_file = request.files['expense_file']
        passbook_file = request.files['passbook_file']
        name = request.form['name']
        account_no = request.form['account_no']
        ifsc = request.form['ifsc']
        details = request.form['details']

        exp_filename = secure_filename(expense_file.filename)
        pass_filename = secure_filename(passbook_file.filename)

        exp_path = os.path.join(app.config['UPLOAD_FOLDER'], exp_filename)
        pass_path = os.path.join(app.config['UPLOAD_FOLDER'], pass_filename)

        expense_file.save(exp_path)
        passbook_file.save(pass_path)

        submission = {
            'name': name,
            'account_no': account_no,
            'ifsc': ifsc,
            'details': details,
            'expense_path': exp_filename,
            'passbook_path': pass_filename
        }

        submissions.append(submission)

        send_email_notification(name, account_no, ifsc, details)

        return redirect(url_for('admin_view'))

    return render_template('upload.html')


@app.route('/admin')
def admin_view():
    return render_template('admin.html', submissions=submissions)


@app.route('/preview/<filename>')
def preview_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename,
                               as_attachment=True)


@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        os.remove(file_path)
        flash(f'{filename} deleted successfully.')
    except FileNotFoundError:
        flash(f'{filename} not found.')

    # Remove from submissions list
    global submissions
    submissions = [
        sub for sub in submissions
        if sub['expense_path'] != filename and sub['passbook_path'] != filename
    ]

    return redirect(url_for('admin_view'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
