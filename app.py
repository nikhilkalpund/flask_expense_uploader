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
ADMIN_PASSWORD = 'admin123'

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

You can view this submission here:
https://flask-expense-uploader.onrender.com/admin
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
        name = request.form['name']
        amount = request.form['amount']
        account_no = request.form['account_no']
        ifsc = request.form['ifsc']
        details = request.form['details']
        passbook_file = request.files['passbook_file']

        if not account_no or not ifsc or not passbook_file:
            flash("Account Number, IFSC Code, and Passbook File are mandatory.")
            return redirect(url_for('upload_form'))

        pass_filename = secure_filename(passbook_file.filename)
        pass_path = os.path.join(app.config['UPLOAD_FOLDER'], pass_filename)
        passbook_file.save(pass_path)

        uploaded_files = []
        for i in range(len(request.files.getlist('expense_files'))):
            file = request.files.getlist('expense_files')[i]
            description = request.form.getlist('descriptions')[i]
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_files.append({'filename': filename, 'description': description})

        submission = {
            'name': name,
            'amount': amount,
            'account_no': account_no,
            'ifsc': ifsc,
            'details': details,
            'files': uploaded_files,
            'passbook_path': pass_filename
        }

        submissions.append(submission)
        send_email_notification(name, account_no, ifsc, details)
        return render_template('confirmation.html')

    return render_template('upload.html')


@app.route('/admin')
def admin_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return render_template('admin.html', submissions=submissions)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_view'))
        else:
            flash("Invalid login")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("Logged out")
    return redirect(url_for('login'))


@app.route('/preview/<filename>')
def preview_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        os.remove(file_path)
        flash(f'{filename} deleted successfully.')
    except FileNotFoundError:
        flash(f'{filename} not found.')

    global submissions
    for sub in submissions:
        sub['files'] = [f for f in sub['files'] if f['filename'] != filename]
        if sub['passbook_path'] == filename:
            sub['passbook_path'] = None
    submissions = [s for s in submissions if s['files'] or s['passbook_path']]
    return redirect(url_for('admin_view'))


if __name__ == '__main__':
    app.run(debug=True)
