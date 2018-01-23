from flask import render_template, flash, redirect, url_for, g, request
from app import app, lm, db, models, babel
from flask_login import current_user, login_user, logout_user, login_required
from .forms import LoginForm, EditForm, RegistrationForm, PostForm
from .oauth import OAuthSignIn, FacebookOAuthSignIn
from .models import User, Post
from datetime import datetime
from config import POSTS_PER_PAGE, LANGUAGES, DATABASE_QUERY_TIMEOUT
from .emails import follower_notifications
from guess_language import guessLanguage
from flask import jsonify
from .translate import translate_text
from flask_sqlalchemy import get_debug_queries

# Things to do and log when the user is logged in
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.add(current_user)
        db.session.commit()
    current_user.locale = get_locale()

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET', 'POST'])
@login_required
def index(page=1):
    form = PostForm()
    if form.validate_on_submit():
        language = guessLanguage(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body = form.post.data, timestamp = datetime.utcnow(), author = current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash('You just said something!')
        return redirect(url_for('index')) # Go back to the page so that hitting the reset button doesn't resubmit the form
    posts = current_user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html', title = 'Muthafuckin', form=form, user=current_user, posts = posts)

@app.route('/login', methods = ['GET', 'POST']) # The methods decorators tell Flask that this view function can get and post requests (otherwise it'll only be GET requests). This needs to bring form data in
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm() # Imports the LoginForm class
    if form.validate_on_submit(): # This validates the data upon submission. Once 'Submit' is hit, it will run the proper validators, attached to the field. Will return 'True' if everything checks out.
        user = User.query.filter_by(nickname=form.login_id.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next') # If someone tried to get to a page without being logged in, then it goes to 'login' and next is the page it would have done to if logged in. Once logged in, it goes back
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        if not user.is_following(user):
            # make the user follow him/herself
            db.session.add(user.follow(user))
            db.session.commit()
        return redirect(next_page)
    # Quickly flashes text to the user. Good for debugging. Needs to be rendered by the template, though.
    # This is the variable for the data that comes from OpenID
    # This is the variable for the data that comes from remember_me
    return render_template('login.html', title = 'Sign In', form = form, providers = app.config['OAUTH_CREDENTIALS'])

# Function to log the user out
@app.route("/logout")
def logout():
    logout_user()
    return redirect('/index')

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first() # Get the user object of the 
    if user == None: # See if the person is available in. Tell'em if they aren't
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    posts = user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html', user = user, posts = posts)

# validate_on_submit checks to see if the POST request worked 
# .data draws out the data that was put into the input
@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(current_user.nickname)
    if form.validate_on_submit():
        current_user.nickname = form.nickname.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = current_user.nickname
        form.about_me.data = current_user.about_me
    return render_template('edit.html', form=form)

# Adding error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback # If this error is called, then the database will be stuck in an invalid state. Need to roll it back.
    return render_template('500.html'), 500

if user is None:
    nickname  = resp.nickname
    if nickname is None or nickname == '':
        nickname = resp.email.split('@')[0]
    nickname = User.make_unique_nickname(nickname)
    user = User(nickname = nickname, email = resp.email)
    db.session.add(user)
    db.session.commit()

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found' % nickname)
        return redirect(url_for('index'))
    if user == current_user:
        flash("You can't follow yourself!")
        return redirect(url_for('user', nickname=nickname))
    u = current_user.follow(user)
    if u is None:
        flash('Cannot follow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are following ' + nickname + '!')
    follower_notifications(user, current_user)
    return redirect(url_for('user', nickname=nickname))

@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found' % nickname)
        return redirect(url_for('index'))
    if user == current_user:
        flash("You can't unfollow yourself!")
        redirect(url_for('user', nickname=nickname))
    u = current_user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You stopped following ' + nickname + '!')
    return redirect(url_for('user', nickname=nickname))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(nickname = form.login_id.data, email = form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Sick dude! Yous a memba')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Register', form = form)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())

@app.route('/translate', methods=['POST'])
@login_required
def translate():
    return jsonify({ 
        'text': translate_text(
            request.form['destLang'], 
            request.form['text']) }) # Using the request.form format, just like we would with an HTML form.

# Deleting a post
@app.route('/delete/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get(id)
    if post is None:
        flash('Post not found')
        return redirect(url_for('index'))
    if post.user_id != current_user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted')
    return redirect(url_for('index'))

@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning("SLOW QUERY: %s \nParameters: %s \nDuration: %fs\nContent: %s\n" % (query.statement, query.parameters, query.duration, query.context))
    return response

# def after_login():
#     if current_user.email is None or current_user.email == "":
#         flash('Invalid login. Please try again.')
#         return redirect(url_for('register'))
#     user = User.query.filter_by(email=current_user.email).first()
#     if user is None:
#         nickname = current_user.nickname
#         if nickname is None or nickname == "":
#             nickname = current_user.email.split('@')[0]
#         nickname = User.make_unique_nickname(nickname)
#         user = User(nickname=nickname, email=current_user.email)
#         db.session.add(user)
#         db.session.commit()
#         # make the user follow him/herself
#         db.session.add(user.follow(user))
#         db.session.commit()
#     remember_me = False
#     if 'remember_me' in session:
#         remember_me = session['remember_me']
#         session.pop('remember_me', None)
#     login_user(user, remember=remember_me)
#     return redirect(request.args.get('next') or url_for('index'))