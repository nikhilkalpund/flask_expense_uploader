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

# Hardcoded admin credentials (for simplicity)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

submissions = []

def send_email_notification(name, account_no, ifsc, details):
    msg = EmailMessage()
    msg['Subject'] = f'New Expense Submission from {name}'
    msg['From'] = 'nikhilkalpund@gmail.com'  # Your sender email
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
            smtp.login('nikhilkalpund@gmail.com', 'pauz qyek jecb iauy')  # Your app password
            smtp.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print("Email failed:", e)

@app.route('/', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        account_no = request.form.get('account_no', '').strip()
        ifsc = request.form.get('ifsc', '').strip()
        details = request.form.get('details', '').strip()

        expense_file = request.files.get('expense_file')
        passbook_file = request.files.get('passbook_file')

        if not account_no or not ifsc:
            flash("Account number and IFSC code are required.")
            return redirect(request.url)

        if not expense_file or expense_file.filename == '':
            flash("Expense file is required.")
            return redirect(request.url)

        if not passbook_file or passbook_file.filename == '':
            flash("Passbook file is required.")
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
            session['admin'] = True
            return redirect(url_for('admin_view'))
        else:
            flash("Invalid credentials.")
    return render_template('admin_login.html')

@app.route('/admin/view')
def admin_view():
    if not session.get('admin'):
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
    if not session.get('admin'):
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
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
