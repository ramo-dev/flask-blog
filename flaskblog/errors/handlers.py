from flask import Flask, render_template, url_for, flash, redirect  

errors = Flask(__name__)

@errors.app_errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(500)
def error_500(error):
    return render_template('errors/404.html'), 500

@errors.app_errorhandler(403)
def error_403(error):
    return render_template('errors/404.html'), 403