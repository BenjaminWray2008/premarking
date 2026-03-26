from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import (DeclarativeBase,
                            Mapped,
                            mapped_column,
                            relationship,
                            Session)
from sqlalchemy import (String,
                        ForeignKey,
                        select,
                        create_engine)
from typing import List
from wtforms import Form, BooleanField, StringField, validators, PasswordField
from flask_login import (UserMixin,
                         LoginManager,
                         login_user,
                         login_required,
                         logout_user,
                         current_user)
from hashlib import sha256
from collections import defaultdict


app = Flask(__name__)
app.config["SECRET_KEY"] = "a-very-secret-secret-key"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


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
    form = Login(request.form)

    if request.method == 'POST':
        print(form.UEmail.data)
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
        return redirect(url_for('profile', user_id=id))
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):

    AdProj = select(UserProject).where(
        UserProject.admin_id == user_id)  # User projects under current admin

    with Session(engine) as session:
        user_projects = session.scalars(AdProj).all()

        projects = []
        for i in user_projects:
            projects.append({
                'id': i.id,
                'user': i.user.name,
                'type': i.project.type,
                'projstand': i.project.id,
                'user_id': i.user.id
            })
    return render_template('profile.html',
                           projects=projects)


@app.route('/admin')
def admin():
    pass


@app.route('/profile/project/<int:project_id>/<int:user_id>')
@login_required
def project(project_id, user_id):
    order = ['A', 'M', 'E']
    standards = {}
    with Session(engine) as session:
        q = select(ProjectStandard).where(
            ProjectStandard.project_id == project_id)
        ProjStand = session.scalars(q).all()

        for standard in ProjStand:
            q = select(Tick).where(
                Tick.standard_id == standard.standard_id)

            Ticks = session.scalars(q).all()

            # standards[standard.standard.name] = sorted([
            #     (i.tier, i.tick) for i in Ticks], key=lambda x: order[x[0]])
            # standards[standard.standard.name] = []
            # for tick in Ticks:
            #     standards[standard.standard.name].append((i.tier, i.tick))

            # standards[standard.standard.name] = sorted([[
            #     i.tick for i in Ticks if i.tier == 'A'], [
            #     i.tick for i in Ticks if i.tier == 'M'], [
            #     i.tick for i in Ticks if i.tier == 'E']])

            groups = defaultdict(list)
            for tick in Ticks:
                groups[tick.tier].append(tick.tick)
            standards[standard.standard.name] = [
                {tier: groups[tier]} for tier in order if groups[tier]]
            
        print(standards)
        

        q = select(Project).where(Project.id == project_id)
        type = session.scalar(q).type
        print(type)

        q = select(User).where(User.id == user_id)
        UData = session.scalar(q)

    return render_template('project.html',
                           standards=standards, type=type, UData=UData)


if __name__ == '__main__':
    app.run(debug=True)
