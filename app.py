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

ADMIN_PANEL_URL = "https://flask-expense-uploader.onrender.com/admin"
submissions = []

def send_email_notification(name, account_no, ifsc, details, amount):
    msg = EmailMessage()
    msg['Subject'] = f'New Expense Submission from {name}'
    msg['From'] = 'nikhilkalpund@gmail.com'  # Replace with your sender email
    recipients = ['kalpundajeet@gmail.com', 'nikhilkalpund@gmail.com']
    msg['To'] = ', '.join(recipients)

    msg.set_content(f'''
A new expense has been submitted:

Name: {name}
Account Number: {account_no}
IFSC Code: {ifsc}
Total Amount: {amount}
Details: {details}

View the expense in the admin panel:
{ADMIN_PANEL_URL}
''')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('nikhilkalpund@gmail.com', 'pauz qyek jecb iauy')  # Use app password
            smtp.send_message(msg)
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

        uploaded_files = request.files.getlist('expense_files[]')
        descriptions = request.form.getlist('file_descriptions[]')

        files_data = []
        for file, desc in zip(uploaded_files, descriptions):
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                files_data.append({'filename': filename, 'description': desc})

        submission = {
            'name': name,
            'amount': amount,
            'account_no': account_no,
            'ifsc': ifsc,
            'details': details,
            'files': files_data
        }
        submissions.append(submission)

        send_email_notification(name, account_no, ifsc, details, amount)

        return render_template('confirmation.html', name=name)

    return render_template('upload.html')

@app.route('/admin')
def admin_view():
    return render_template('admin.html', submissions=submissions)

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
    submissions = [
        sub for sub in submissions
        if all(f['filename'] != filename for f in sub.get('files', []))
    ]

    return redirect(url_for('admin_view'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
