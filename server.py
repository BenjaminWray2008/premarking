from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import (DeclarativeBase,
                            Mapped,
                            mapped_column,
                            relationship,
                            Session)
from sqlalchemy import String, ForeignKey, select, create_engine
from typing import List

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('login.html')
    return redirect(url_for('login'))


@app.route('/login')
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
