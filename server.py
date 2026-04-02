from flask import (Flask,
                   render_template,
                   redirect,
                   url_for,
                   request,
                   session,
                   jsonify)
from sqlalchemy.orm import (DeclarativeBase,
                            Mapped,
                            mapped_column,
                            relationship,
                            Session)
from sqlalchemy import (String,
                        ForeignKey,
                        select,
                        create_engine)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from typing import List
from wtforms import (Form,
                     BooleanField,
                     StringField,
                     validators,
                     PasswordField,
                     SelectField,
                     SubmitField)
from flask_login import (UserMixin,
                         LoginManager,
                         login_user,
                         login_required,
                         logout_user,
                         current_user)
from hashlib import sha256
from collections import defaultdict
from weasyprint import HTML, CSS
import smtplib
from email.message import EmailMessage
import csv
from flask_wtf.file import FileField, FileAllowed, FileRequired

app = Flask(__name__)
app.config["SECRET_KEY"] = "a-very-secret-secret-key"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'User'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    year_level: Mapped[int]
    admin: Mapped[bool]

    user_projects: Mapped[List["UserProject"]] = relationship(
        "UserProject", back_populates="user")


class Project(Base):
    __tablename__ = 'Project'
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))

    user_projects: Mapped[List["UserProject"]] = relationship(
        "UserProject", back_populates="project")

    standard_projects: Mapped[List["ProjectStandard"]] = relationship(
        "ProjectStandard", back_populates="project")


class UserProject(Base):
    __tablename__ = 'UserProject'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("User.id"))

    project_id: Mapped[int] = mapped_column(
        ForeignKey("Project.id"))

    admin_id: Mapped[int] = mapped_column(
        ForeignKey("Admin.id"))

    github: Mapped[str] = mapped_column(String(50))
    doc: Mapped[str] = mapped_column(String(50))
    marked: Mapped[bool]

    user: Mapped["User"] = relationship(
        "User", back_populates="user_projects")

    project: Mapped["Project"] = relationship(
        "Project", back_populates="user_projects")

    admin: Mapped[List['Admin']] = relationship(
        "Admin", back_populates='userproject')


class Admin(Base, UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    __tablename__ = 'Admin'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50))
    hash: Mapped[str]

    userproject: Mapped[List['UserProject']] = relationship(
        "UserProject", back_populates='admin')


class Standard(Base):
    __tablename__ = 'Standard'
    standard_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    level: Mapped[int]
    number: Mapped[int]
    credit: Mapped[int]

    standard_projects: Mapped[List["ProjectStandard"]] = relationship(
        "ProjectStandard", back_populates="standard")

    ticks: Mapped[List["Tick"]] = relationship(
        "Tick", back_populates='standard')


class ProjectStandard(Base):
    __tablename__ = 'ProjectStandard'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("Project.id"))

    standard_id: Mapped[int] = mapped_column(
        ForeignKey("Standard.standard_id"))

    project: Mapped["Project"] = relationship(
        "Project", back_populates="standard_projects")

    standard: Mapped["Standard"] = relationship(
        "Standard", back_populates="standard_projects")


class Tick(Base):
    __tablename__ = 'Tick'
    standard_id: Mapped[int] = mapped_column(
        ForeignKey("Standard.standard_id"))

    id: Mapped[int] = mapped_column(primary_key=True)
    tick: Mapped[str] = mapped_column(String(50))
    tier: Mapped[str] = mapped_column(String(50))

    standard: Mapped["Standard"] = relationship(
        'Standard', back_populates='ticks')


engine = create_engine("sqlite:///instance/database.db")
# Base.metadata.create_all(engine)


class Login(Form):
    UEmail = StringField('Email:', validators=[validators.InputRequired()])
    UPass = PasswordField('Password:', validators=[validators.InputRequired()])


class NewUser(FlaskForm):
    file = FileField('Browse Files:', validators=[
        FileRequired(), FileAllowed(['csv'], 'CSV only')
        ])
    dropdown = SelectField('Select', choices=[])
    upload = SubmitField('Upload')


def submit(ticks):
    return 'hi'


def turn_to_pdf(html, email):
    css = CSS(filename='static/css/style.css')
    html = HTML(string=html)
    html.write_pdf(email, stylesheets=[css])


def send_email(email, path, proj_type, assess_num, user_name):
    msg = EmailMessage()
    msg['Subject'] = f'Feedback for {assess_num}'
    msg['From'] = 'premarkingsoftware@gmail.com'
    msg['To'] = email
    msg.set_content(f"""Hi {user_name},
                     here's some feedback for your {proj_type}
                     project ({assess_num}) :)""")

    with open(path, 'rb') as f:
        pdf = f.read()
        msg.add_attachment(pdf, maintype='application',
                           subtype='pdf', filename='file.pdf')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('premarkingsoftware@gmail.com', 'tbub hjpc dgzu cpjl')
        smtp.send_message(msg)


def standard_data(project_id, user_id):
    cor = {'Achieved': 'green', 'Merit': 'blue', 'Excellence': 'yellow'}
    order = ['Achieved', 'Merit', 'Excellence']
    standards = {}

    with Session(engine) as sql_session:
        q = select(ProjectStandard).where(
            ProjectStandard.project_id == project_id)
        ProjStand = sql_session.scalars(q).all()

        for standard in ProjStand:
            q = select(Tick).where(
                Tick.standard_id == standard.standard_id)

            Ticks = sql_session.scalars(q).all()

            groups = defaultdict(list)
            for tick in Ticks:
                groups[tick.tier].append(tick.tick)

            sn = str(standard.standard.name)
            snu = str(standard.standard.number)

            standards[sn + ' ' + snu] = [
                {(tier, cor[tier]): groups[tier]}
                for tier in order if groups[tier]
                  ]
        print(standards)

        q = select(Project).where(Project.id == project_id)
        type = sql_session.scalar(q).type

        q = select(User).where(User.id == user_id)
        UData = sql_session.scalar(q)
    return (UData, type, standards, snu)


def new_user(file, selected):
    stream = file.stream.read().decode("utf-8").splitlines()

    reader = csv.reader(stream)
    with Session(engine) as sql_session:
        for index, row in enumerate(reader):
            if index == 0:
                continue
            id = row[0]
            surname = row[1]
            first_name = row[2]
            year_level = row[4]

            q = select(User).where(User.id == id)
            exist = sql_session.scalar(q)

            q = select(Project).where(Project.type == selected)
            project_id = sql_session.scalar(q).id

            q = select(UserProject).where(
                UserProject.user_id == id).where(
                    UserProject.project_id == project_id
                    ).where(UserProject.admin_id == current_user.id)
            proj_exist = sql_session.scalar(q)

            if proj_exist:
                print('already done')
                continue

            new_project = UserProject(
                user_id=id, project_id=project_id,
                admin_id=current_user.id)
            db.session.add(new_project)

            if exist:
                continue

            user = User(id=id, name=f"{first_name} {surname}",
                        year_level=year_level,
                        email=f'{id}@buurnside.school.nz', admin=False)
            db.session.add(user)

        db.session.commit()
    return 'hi'


@login_manager.user_loader
def load_user(user_id):
    query = select(Admin).where(Admin.id == user_id)
    with Session(engine) as session:
        obj = session.scalar(query)
    return obj


@app.route('/', methods=['POST', 'GET'])
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    print(current_user)
    form = Login(request.form)

    if request.method == 'POST':
        UEmail = form.UEmail.data
        UPass = form.UPass.data

        q = select(Admin).where(Admin.email == UEmail)
        with Session(engine) as session:
            creds = session.scalar(q)

        id = creds.id
        hash = creds.hash
        h = sha256()
        h.update(UPass.encode())
        hashed = h.hexdigest()
        if hashed != hash:
            return render_template('login.html', form=form)

        user = Admin(id=id, username=UEmail)
        login_user(user)
        return redirect(url_for('profile'))
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/instructions', methods=['POST', 'GET'])
@login_required
def instructions():
    form = NewUser()
    with Session(engine) as sql_session:
        q = select(Project)
        project_types = sql_session.scalars(q).all()

    form.dropdown.choices = [i.type for i in project_types]

    if form.validate_on_submit():
        file = form.file.data
        selected = form.dropdown.data
        print("VALID FILE:", file, selected)
        new_user(file, selected)

    else:
        if request.method == 'POST':
            print("ERRORS:", form.errors)

    return render_template('instructions.html', form=form)


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():

    AdProj = select(UserProject).where(
        UserProject.admin_id == current_user.id)
    # User projects under current admin
    with Session(engine) as session:
        user_projects = session.scalars(AdProj).all()
        marked_count = 0
        unmarked_count = 0
        projects = []
        for i in user_projects:
            if i.marked == 1:
                premarked = 'Premarked'
                marked_count += 1
            else:
                premarked = 'Unmarked'
                unmarked_count += 1

            projects.append({
                'id': i.id,
                'user': i.user.name,
                'type': i.project.type,
                'projstand': i.project.id,
                'user_id': i.user.id,
                'marked': premarked
            })
    return render_template('profile.html',
                           projects=projects, searchBar=True,
                           counts=(marked_count, unmarked_count))


@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    q = request.args.get("q", "")
    data = []
    with Session(engine) as sql_session:
        user_ids = sql_session.scalars(
            select(User).where(User.name.contains(q))).all()
        for user in user_ids:
            user_id = user.id
            result = sql_session.scalar(select(UserProject).where(
                UserProject.user_id == user_id).where(
                    UserProject.admin_id == current_user.id))
            data.append({
             'id': result.user_id
            })
    print(data)
    return jsonify(data)


@app.route('/project/<int:project_id>/<int:user_id>', methods=['POST', 'GET'])
@login_required
def project(project_id, user_id):

    if request.method == 'POST':
        tickValues = request.form.getlist("ticks")
        form_data = request.form.to_dict()
        textValues = {}
        for key, value in form_data.items():
            if key.startswith("texts["):
                text = key[6:-1]
                textValues[text] = value

        session['texts'] = textValues
        session["ticks"] = tickValues
        return redirect(url_for('clean',
                                project_id=project_id, user_id=user_id))

    UData, type, standards, snu = standard_data(project_id, user_id)
    return render_template('project.html',
                           standards=standards, type=type,
                           UData=UData, snu=snu)


@app.route('/clean/<int:project_id>/<int:user_id>')
@login_required
def clean(project_id, user_id):
    tickValues = session.get('ticks', [])
    textValues = session.get('texts', [])
    UData, type, standards, snu = standard_data(project_id, user_id)

    html = render_template('clean.html',
                           standards=standards, type=type,
                           UData=UData, tickValues=tickValues,
                           textValues=textValues)

    q = select(User).where(User.id == user_id)
    with Session(engine) as sql_session:
        user = sql_session.scalar(q)
    email = user.email
    path = 'email.pdf'
    turn_to_pdf(html, path)
    send_email(email, path, type, snu, UData.name)
    print('EMAIL SENT')

    return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(debug=True)
