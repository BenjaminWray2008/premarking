from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import (DeclarativeBase,
                            Mapped,
                            mapped_column,
                            relationship,
                            Session)
from sqlalchemy import String, ForeignKey, select, create_engine
from typing import List
from wtforms import Form, BooleanField, StringField, validators, PasswordField
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from hashlib import sha256


app = Flask(__name__)
app.config["SECRET_KEY"] = "a-very-secret-secret-key"
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"


class Base(DeclarativeBase):
    pass


class User(Base, UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username
        
    __tablename__ = 'User'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    year_level: Mapped[int]
    email: Mapped[str] = mapped_column(String(50))
    admin: Mapped[bool]
    user_projects: Mapped[List["UserProject"]] = relationship("UserProject", back_populates="user")


class Project(Base):
    __tablename__ = 'Project'
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    user_projects: Mapped[List["UserProject"]] = relationship("UserProject", back_populates="project")
    standard_projects: Mapped[List["ProjectStandard"]] = relationship("ProjectStandard", back_populates="project")


class UserProject(Base):
    __tablename__ = 'UserProject'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.id"))
    project_id: Mapped[int] = mapped_column(ForeignKey("Project.id"))
    github: Mapped[str] = mapped_column(String(50))
    doc: Mapped[str] = mapped_column(String(50))
    admin_id: Mapped[int] = mapped_column(ForeignKey("Admin.id"))
    user: Mapped["User"] = relationship("User", back_populates="user_projects")
    project: Mapped["Project"] = relationship("Project", back_populates="user_projects")
    admin: Mapped[List['Admin']] = relationship("Admin", back_populates='userproject')

    def repr():
        print(67)
        
        
class Admin(Base):
    __tablename__ = 'Admin'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50))
    hash: Mapped[str]
    userproject: Mapped[List['UserProject']] = relationship("UserProject", back_populates='admin')


class Standard(Base):
    __tablename__ = 'Standard'
    standard_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    credit: Mapped[int]
    standard_projects: Mapped[List["ProjectStandard"]] = relationship("ProjectStandard", back_populates="standard")
    ticks: Mapped[List["Tick"]] = relationship("Tick", back_populates='standard')


class ProjectStandard(Base):
    __tablename__ = 'ProjectStandard'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("Project.id"))
    standard_id: Mapped[int] = mapped_column(ForeignKey("Standard.standard_id"))
    project: Mapped["Project"] = relationship("Project", back_populates="standard_projects")
    standard: Mapped["Standard"] = relationship("Standard", back_populates="standard_projects")


class Tick(Base):
    __tablename__ = 'Tick'
    standard_id: Mapped[int] = mapped_column(ForeignKey("Standard.standard_id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    tick: Mapped[str] = mapped_column(String(50))
    standard: Mapped["Standard"] = relationship('Standard', back_populates='ticks')


engine = create_engine("sqlite:///instance/database.db")
# Base.metadata.create_all(engine)


class Login(Form):
    UEmail = StringField('Email:', validators=[validators.InputRequired()])
    UPass = PasswordField('Password:', validators=[validators.InputRequired()])


@login_manager.user_loader
def load_user(user_id):
    query = select(User).where(User.id == user_id)
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
            
        id = creds.id; hash = creds.hash
        h = sha256()
        h.update(UPass.encode())
        hashed = h.hexdigest()
        if hashed != hash:
            return render_template('login.html', form=form)
        
        user = User(id=id, username=UEmail)
        login_user(user)
        
        print('yippe')
        query = select(UserProject).where(UserProject.admin_id == id)
        with Session(engine) as session:
            user_projects = session.scalars(query).all()
            print(user_projects, user_projects[0].project.type)
       
            projects = [{
                'id': i.id,
                'user': i.user.name,
                'type': i.project.type,
            } for i in user_projects]
        print(projects)

        return render_template('profile.html', projects=projects)
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name='bob')
    

@app.route('/admin')
def admin():
    pass
    

@app.route('/project/<int:project_id>')
@login_required 
def project(project_id):
    return render_template('project.html', id=project_id)


if __name__ == '__main__':
    app.run(debug=True)
