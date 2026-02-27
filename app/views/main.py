from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/databases')
def databases():
    return render_template('databases.html')

@main_bp.route('/query')
def query():
    return render_template('query.html')

@main_bp.route('/tasks')
def tasks():
    return render_template('tasks.html')
