# Import necessary modules and packages
from flaskblog import app, db, bcrypt, mail
from flaskblog.models import User, Post
import secrets, os
from PIL import Image
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flaskblog.forms import (
    RegistrationForm, LoginForm, UpdateAccountForm, PostForm,
    ResetPasswordForm, RequestResetForm
)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from dotenv import load_dotenv
load_dotenv()

# Home and About Routes
@app.route("/")
@app.route("/home")
def home():
    """
    Route for the home page, displaying paginated posts.
    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=6)
    return render_template("home.html", posts=posts)

@app.route("/about")
def about():
    """
    Route for the about page.
    """
    return render_template("about.html", title="About")

# User Registration and Authentication Routes
@app.route("/register", methods=['GET', 'POST'])
def register():
    """
    Allow users to register for a new account.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f"Your account has been created! You are now able to log in.", 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    Allow users to log in to their account.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Login unsuccessful. Please check email and password.", 'danger')
    return render_template("login.html", title="Login", form=form)

@app.route("/logout")
def logout():
    """
    Log out the user.
    """
    logout_user()
    return redirect(url_for('home'))

# Account Management Routes
def save_picture(form_picture):
    """
    Helper function to save and resize the user's profile picture.
    """
    # Generate a unique filename for the profile picture
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    # Resize the profile picture
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """
    Allow users to manage their account details, including profile picture.
    """
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template("account.html", title="Account", image_file=image_file, form=form)

# Blog Post Management Routes
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    """
    Allow users to create new blog posts.
    """
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title="New Post", form=form, legend='New Post')

@app.route("/post/<int:post_id>")
def post(post_id):
    """
    Display a single blog post.
    """
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    """
    Allow users to update their blog posts.
    """
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your post has been updated!", "success")
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    """
    Allow users to delete their blog posts.
    """
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")
    return redirect(url_for('home'))

# User-Specific Blog Posts Route
@app.route("/user/<string:username>")
def user_posts(username):
    """
    Display blog posts of a specific user.
    """
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template("user_posts.html", posts=posts, user=user)

# Password Reset Routes
def send_reset_email(user):
    """
    Send a password reset email to the user.
    """
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreplyfbtest@gmail.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
    '''
    with app.app_context():
        with mail.connect() as conn:
            conn.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    """
    Request a password reset.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        else:
            flash('No user with that email address exists.', 'danger')
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    """
    Validate and process a password reset token.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f"Your password has been updated! You are now able to log in.", 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# Activity Feed Route
@app.route("/activity-feed")
def activity_feed():
    """
    Display an activity feed of posts by the current user.
    """
    posts = Post.query.filter_by(author=current_user).all()
    return render_template("activity_feed.html", posts=posts)

# Error Handling Routes
@app.errorhandler(404)
def error_404(error):
    """
    Handle 404 errors.
    """
    flash('Page not found', 'danger')
    return redirect(url_for('home'))

@app.errorhandler(500)
def error_500(error):
    """
    Handle 500 errors.
    """
    flash('Internal server error', 'danger')
    return redirect(url_for('home'))

@app.errorhandler(403)
def error_403(error):
    """
    Handle 403 errors.
    """
    flash('Access forbidden', 'danger')
    return redirect(url_for('home'))
