from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, session
import os
from werkzeug.utils import secure_filename
from email.message import EmailMessage
import smtplib

app = Flask(__name__, static_folder='uploads')
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'
ADMIN_PANEL_URL = 'https://flask-expense-uploader.onrender.com/admin'

submissions = []


def send_email_notification(name, account_no, ifsc, details):
    msg = EmailMessage()
    msg['Subject'] = f'New Expense Submission from {name}'
    msg['From'] = 'nikhilkalpund@gmail.com'

    recipients = ['kalpundajeet@gmail.com', 'nikhilkalpund@gmail.com']
    msg['To'] = ', '.join(recipients)

    msg.set_content(f'''
A new expense has been submitted:

Name: {name}
Account Number: {account_no}
IFSC Code: {ifsc}
Details: {details}

You can view it in the admin panel here:
{ADMIN_PANEL_URL}
''')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('nikhilkalpund@gmail.com', 'pauz qyek jecb iauy')
            smtp.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print("Email failed:", e)


@app.route('/', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'POST':
        expense_file = request.files.get('expense_file')
        passbook_file = request.files.get('passbook_file')
        name = request.form.get('name')
        account_no = request.form.get('account_no')
        ifsc = request.form.get('ifsc')
        details = request.form.get('details')

        if not (expense_file and passbook_file and account_no and ifsc):
            flash("All fields are required, including both file uploads.")
            return redirect(request.url)

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

        return render_template('confirmation.html')

    return render_template('upload.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_view'))
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')


@app.route('/admin-panel')
def admin_view():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html', submissions=submissions)


@app.route('/preview/<filename>')
def preview_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/delete/<filename>')
def delete_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        os.remove(file_path)
        flash(f'{filename} deleted successfully.')
    except FileNotFoundError:
        flash(f'{filename} not found.')

    global submissions
    submissions = [
        sub for sub in submissions
        if sub['expense_path'] != filename and sub['passbook_path'] != filename
    ]

    return redirect(url_for('admin_view'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully.')
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)
