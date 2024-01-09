# Import necessary modules and packages
from flaskblog import app, db, bcrypt, mail
from flaskblog.models import User, Post
import secrets, os
from PIL import Image
from flask import Flask, render_template, url_for, flash, redirect, request, abort, jsonify
from flaskblog.forms import (
    RegistrationForm, LoginForm, UpdateAccountForm, PostForm,
    ResetPasswordForm, RequestResetForm
)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from dotenv import load_dotenv
from flaskblog.models import Message
from flaskblog.forms import MessageForm
from flask_socketio import emit, SocketIO
from flaskblog import socketio

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


@app.route("/send_message/<recipient_username>", methods=['GET', 'POST'])
@login_required
def send_message(recipient_username):
    form = MessageForm()
    user = User.query.filter_by(username=current_user.username).first()
    received_messages = Message.query.filter_by(recipient=user).all()
    sent_messages = Message.query.filter_by(sender=user).all()
    users = User.query.all()
    previous_messages = [message.body for message in received_messages]  # Get previous messages from the database

    recipient = User.query.filter_by(username=recipient_username).first()
    # Check if the user exists
    if not recipient:
        abort(404)

    if form.validate_on_submit():
        message = Message(
            title=form.title.data,
            body=form.body.data,
            sender=user,
            recipient=recipient
        )
        db.session.add(message)
        db.session.commit()
        flash("Message Sent", "success")
        socketio.emit('receive_message', {'message': message.body}, room=recipient.username)
        return redirect(url_for(
            'send_message',
            recipient_username=recipient.username
        ))
    
    # Send user details and previous messages to the client
    socketio.emit('user_details', {
        'recipient': {
            'username': recipient.username,
            'profile_picture': recipient.image_file
        },
        'previous_messages': previous_messages
    }, room=current_user.username)

    return render_template('send_message.html',
                           title="New Message",
                           form=form,
                           recipient=recipient,
                           recipient_username=recipient_username,
                           received_messages=received_messages,
                           sent_messages=sent_messages,
                           users=users)
    

@app.route("/inbox")
@login_required
def inbox():
    received_messages = current_user.received_messages.order_by(Message.timestamp.desc())
    users = User.query.filter(User.id != current_user.id).all()  # Exclude the current user from the list
    return render_template('inbox.html', title='Inbox', user=current_user, messages=received_messages, users=users)




@app.route('/search', methods=['GET'])
def search():
    term = request.args.get('term')
    users = User.query.filter(User.username.ilike(f'%{term}%')).all()
    posts = Post.query.filter(Post.title.ilike(f'%{term}%')).all()

    usernames = [user.username for user in users]
    post_titles = [post.title for post in posts]
    post_ids = [post.id for post in posts]
    profile_pics = [User.query.get(post.user_id).image_file for post in posts]  # Fetch profile pics based on user_id
    dates = [post.date_posted.strftime('%Y-%m-%d') for post in posts]  # Format date as needed

    print("Usernames:", usernames)
    print("Post Titles:", post_titles)
    print("Post IDs:", post_ids)
    print("Profile Pics:", profile_pics)
    print("Dates:", dates)

    return jsonify({
        'usernames': usernames,
        'postTitles': post_titles,
        'postIDs': post_ids,
        'profilePics': profile_pics,
        'dates': dates
    })



@app.route('/search-page')
def search_page():
    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)


@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


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