from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='uploads')
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

submissions = []

@app.route('/', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'POST':
        expense_file = request.files['expense_file']
        passbook_file = request.files['passbook_file']
        name = request.form['name']
        account_no = request.form['account_no']
        ifsc = request.form['ifsc']
        details = request.form['details']

        exp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(expense_file.filename))
        pass_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(passbook_file.filename))
        expense_file.save(exp_path)
        passbook_file.save(pass_path)

        submission = {
            'name': name,
            'account_no': account_no,
            'ifsc': ifsc,
            'details': details,
            'expense_path': exp_path,
            'passbook_path': pass_path
        }

        submissions.append(submission)
        return redirect(url_for('admin_view'))

    return render_template('upload.html')

@app.route('/admin')
def admin_view():
    return render_template('admin.html', submissions=submissions)

if __name__ == '__main__':
    app.run()
