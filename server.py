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
from flask_login import UserMixin

app = Flask(__name__)
app.config["SECRET_KEY"] = "a-very-secret-secret-key"


class Base(DeclarativeBase):
    pass


class User(Base):
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
    admin_id: Mapped[int] = mapped_column(ForeignKey("User.id"))
    user: Mapped["User"] = relationship("User", back_populates="user_projects")
    project: Mapped["Project"] = relationship("Project", back_populates="user_projects")
    admin: Mapped[List['Admin']] = relationship("Admin", back_populates='userproject')


class Admin(Base):
    __tablename__ = 'Admin'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50))
    hash: Mapped[str] = mapped_column(String(50))
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
    UName = StringField('Name', validators=[validators.InputRequired()])
    UPass = PasswordField('Password', validators=[validators.InputRequired()])


def run_q(q):
    pass
    


@app.route('/', methods=['POST', 'GET'])
def home():
    
    return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = Login(request.form)
    if request.method == 'POST':
        print(form.UName.data)
        query = select(User)
        return redirect(url_for('profile'))
    return render_template('login.html', form=form)


@app.route('/profile')
def profile():
    return render_template('profile.html', name='bob', projects=(['jimmy', 'prog'], ['bob', 'design']))
    

@app.route('/admin')
def admin():
    pass
    
    
@app.route('/project/<int:project_id>')
def project(project_id):
    return render_template('project.html', id=project_id)


if __name__ == '__main__':
    app.run(debug=True)
