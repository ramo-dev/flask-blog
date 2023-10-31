#Flask Blog App
Table of Contents

    Description
    Features
    Demo
    Installation
    Usage
    Contributing
    License
    Contact

Description

A Flask-based blog application for creating, managing, and sharing your blog posts.

Screenshot
Features

    User registration and authentication
    Create, edit, and delete blog posts
    User profile with customizable avatars
    Responsive design
    ...

Demo

Link to Live Demo
Installation

    Clone the repository:

    bash

git clone https://github.com/yourusername/your-blog-app.git

Change into the project directory:

bash

cd your-blog-app

Create a virtual environment and activate it:

bash

python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

Install the required packages:

bash

pip install -r requirements.txt

Create a .env file with your configuration settings:

env

FLASK_APP=run.py
FLASK_ENV=development  # or production for a production environment
SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=your_database_uri

Initialize the database:

bash

flask db init
flask db migrate -m "Initial migration"
flask db upgrade

Start the application:

bash

    flask run

    Open a web browser and go to http://localhost:5000.

Usage

    Visit the homepage to view and create blog posts.
    Sign up or log in to manage your profile and create posts.
    Customize your user profile by uploading an avatar.
    ...

Contributing

    Fork the repository.
    Create a new branch for your feature: git checkout -b feature-name
    Commit your changes: git commit -m 'Add some feature'
    Push to the branch: git push origin feature-name
    Open a Pull Request.

License

This project is licensed under the MIT License. See the LICENSE file for details.
Contact

    Author: Ramo-dev
    GitHub: https://github.com/ramo-dev
    Email: annuar.dev@gmail.com
