from app import db, lm # import the database
from flask_login import UserMixin
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
import sys # For the database

if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask_whooshalchemy as whooshalchemy

# Creating a followers table
followers = db.Table('followers', 
                    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
                    db.Column('followed_id', db.Integer, db.ForeignKey('users.id')))

class Post(db.Model):
    __searchable__ = ['body']

    id = db.Column(db.Integer, autoincrement=True, primary_key = True)
    body = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) # Get the element from another class
    timestamp = db.Column(db.DateTime)
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post % r>' % (self.body)  # Tells how to print objects of this class, used for debugging

if enable_search:
    whooshalchemy.whoosh_index(app, Post) # Start the indexing process to search

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    social_id = db.Column(db.String(64), nullable=True, unique=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), nullable=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic') # Sets up a one-to-many relationship from authors to posts
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime) # When the user was last seen
    # Defining the followers many-to-many relationship
    followed = db.relationship('User', # Matches a left-side user to a right-side user
                                secondary=followers, # This is the table used for associations
                                primaryjoin=(followers.c.follower_id == id), # Left side of the join
                                secondaryjoin=(followers.c.followed_id == id), # Right side of the join
                                backref=db.backref('followers', lazy='dynamic'), # Gives the people someone follows, rather than the followers someone has 
                                lazy='dynamic') # 'Dynamic' means the query doesn't run until you want it to
    
    # Importing avatars (pictures) into the user profile
    def avatar(self, size):
        return 'https://scontent-sea1-1.xx.fbcdn.net/v/t1.0-1/c0.43.240.240/p240x240/24131240_10210304380259338_4733926116983322399_n.jpg?oh=3b5e3c402bed835ee4d1513112e4d86b&oe=5ABDBE45'

    def __repr__(self): # pragma: no cover
        return '<User % r>' % (self.nickname)  # Tells how to print objects of this class, used for debugging
    
    @staticmethod # Static methods are methods that apply to any instance of the class
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname
    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())

    # For generating and checking passwords
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Retrieve the user ID and convert it to and int
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))