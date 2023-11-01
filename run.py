from flaskblog import app

if __name__ == '__main__':

    app.app_context().push()

    # Run the Flask application
<<<<<<< HEAD
    app.run(debug=False,host='0.0.0.0', port=80)
=======
    app.run(debug=False, host='0.0.0.0')
>>>>>>> refs/remotes/origin/main
