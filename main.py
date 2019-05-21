import uuid
import os
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from datetime import date


UPLOAD_FOLDER = 'img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


app = Flask(__name__)
app.secret_key = b'237rh[112*-whf912=-`][wf9q89w'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)


if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    father_name = db.Column(db.String(80))
    father_surname = db.Column(db.String(80))
    mother_name = db.Column(db.String(80))
    mother_surname = db.Column(db.String(80))
    phone = db.Column(db.String(80), nullable=False)
    school = db.Column(db.String(80), nullable=False)
    grade = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(160), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    photo = db.Column(db.String(80), nullable=False)
    language = db.Column(db.String(80), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))

    def __repr__(self):
        return '<Student %s %s>' % (self.name, self.surname)


class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    date = db.Column(db.String(80), nullable=True)
    students = db.relationship('Student', backref="exam", lazy='dynamic')


@app.route('/exams')
def exams():
    exams = Exam.query.all()
    return render_template('exams.html', exams=exams)


@app.route('/')
def index():
    return redirect(url_for('exams'))


@app.route('/add-exam', methods=['POST'])
def add_exam():
    exam_name = request.form.get('exam_name')
    if not exam_name:
        flash("Invalid Exam Name")
        return 
    exam_description = request.form.get('exam_description')
    exam_date = request.form.get('exam_date')
    exam = Exam(name=exam_name, description=exam_description, date=exam_date)
    db.session.add(exam)
    db.session.commit()

    print(exam_name)
    print(exam_description)
    print(exam_date)
    return redirect(url_for('exams'))


@app.route('/edit-exam/<int:exam_id>', methods=['GET', 'POST'])
def edit_exam(exam_id):
    exam = Exam.query.get(exam_id)
    if exam is None:
        flash("No such exam with ID=%s" % exam_id)
        return

    if request.method == 'GET':
        return render_template('edit_exam.html', exam=exam)

    elif request.method == 'POST':
        exam_name = request.form.get('exam_name')
        exam_description = request.form.get('exam_description')
        exam_date = request.form.get('exam_date')
        if not exam_name:
            flash('Invalid Exam Name')

        exam.name = exam_name
        exam.description=exam_description
        exam.date = exam_date
        db.session.commit()

        flash("Exam edited successfully!")
        return redirect(url_for('exams'))


@app.route('/register-student/<int:exam_id>')
def register_student(exam_id):
    exam = Exam.query.get(exam_id)
    if exam is None:
        return "No exam with ID=%s" % exam_id, 404
    return render_template('register_student.html', exam=exam, title="Register")


@app.route('/add_student/<int:exam_id>', methods=['POST'])
def add_student(exam_id):
    form = request.form

    exam=Exam.query.get(exam_id)
    if exam is None:
        return "No such exam with ID=%s" % exam_id

    required = ['name', 'surname', 'grade', 'school', 'birthday', 'address']
    for r in required:
        if not form.get(r):
            flash('Please fill %s.' % r)
            return redirect(url_for('register'))

    name = form.get('name')
    surname = form.get('surname')
    father_name = form.get('father_name')
    father_surname = form.get('father_surname')
    mother_name = form.get('mother_name')
    mother_surname = form.get('mother_surname')
    phone = form.get('phone')
    birthday = date(*map(int, form.get('birthday').split('-')))
    address = form.get('address')
    school = form.get('school')
    grade = form.get('grade')
    language = form.get('language')

    if 'photo' not in request.files:
        flash('No file part')
        return redirect(url_for('register'))
    file = request.files['photo']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        flash('Please select photo')
        print('Please select photo')
        return redirect(url_for('register'))
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        flash("Invalid photo")
        print("Invalid photo")
        return redirect(url_for('register'))

    student = Student(name=name, surname=surname, father_name=father_name, father_surname=father_surname,
                      mother_name=mother_name, mother_surname=mother_surname, phone=phone, birthday=birthday,
                      address=address, school=school, grade=grade, photo=filename, language=language,
                      exam_id=exam_id)
    db.session.add(student)
    db.session.commit()
    print("Added student successfully.")
    flash("Added student successfully.")
    return redirect(url_for('badge', student_id=student.id))


@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get(student_id)
    print("student surname", student.surname)
    if student is None:
        flash("No such student")
        return "404 not found", 404

    if request.method == 'GET':
        delete_url = url_for('delete_student', student_id=student_id)
        return render_template('edit_student.html', student=student, 
                title="Edit Student", delete_url=delete_url)

    if request.method == 'POST':
        form = request.form
        name = form.get('name')
        surname = form.get('surname')
        father_name = form.get('father_name')
        father_surname = form.get('father_surname')
        mother_name = form.get('mother_name')
        mother_surname = form.get('mother_surname')
        phone = form.get('phone')


        if form.get('birthday'): birthday = date(*map(int, form.get('birthday').split('-')))
        else: birthday = None

        language = form.get('language')
        address = form.get('address')
        school = form.get('school')
        grade = form.get('grade')

        required = ['name', 'surname', 'grade', 'school', 'birthday', 'address']
        for r in required:
            if not form.get(r):
                flash('Please fill %s.' % r)
                return redirect(url_for('edit_student', student_id=student_id))

        student.name = name
        student.surname = surname
        student.father_surname = father_surname
        student.father_name = father_name
        student.mother_name = mother_name
        student.mother_surname = mother_surname
        student.phone = phone
        student.birthday = birthday
        student.address = address
        student.school = school
        student.grade = grade
        student.language = language

        if 'photo' in request.files:
            file = request.files['photo']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()

                # delete older photo
                try:
                    if student.photo:
                        old_photo = os.path.join(app.config['UPLOAD_FOLDER'], student.photo)
                        os.remove(old_photo)
                except Exception as e:
                    print("Unable to remove old photo: %s" % e)

                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                student.photo = filename
            elif file:
                flash("Invalid photo")
                return redirect(url_for('edit_student', student_id=student_id))

        db.session.commit()
        flash("Student edited successfully.")
        return redirect(url_for('edit_student', student_id=student_id))


@app.route('/badge/<int:student_id>')
def badge(student_id):
    student = Student.query.get(student_id)
    return render_template('badge.html', student=student, title="Badge")


@app.route('/students/<int:exam_id>')
def students(exam_id):
    exam = Exam.query.get(exam_id)
    if exam is None:
        return "No exam with ID=%s" % exam_id, 404
    students = Student.query.filter_by(exam_id=exam_id)
    return render_template('students.html', students=students, title="Students", exam=exam)


@app.route('/delete_student/<int:student_id>')
def delete_student(student_id):
    student = Student.query.get(student_id)
    if student is None:
        return "Student not found!", 404
    db.session.delete(student)
    db.session.commit()
    flash("Student %s %s %06d deleted successfully." % (student.name, student.surname, student_id))
    return redirect(url_for('students'))


@app.route('/student_photo/<filename>')
def student_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
