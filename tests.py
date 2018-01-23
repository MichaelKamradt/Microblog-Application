# !flask/bin/python

import os
import unittest

from config import basedir
from app import app, db
from app.translate import translate_text
from app.models import User, Post
from datetime import datetime, timedelta

# Setting up coverage
from coverage import coverage
cov = coverage(branch=True, omit=['flask/*', 'tests.py'])
cov.start()

class TestCase(unittest.TestCase): # This is a class that holds setUp and Teardown
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_avatar(self):
        u = User(nickname='john', email='john@example.com')
        avatar = u.avatar(128)
        expected = 'https://scontent-sea1-1.xx.fbcdn.net/v/t1.0-1/c0.43.240.240/p240x240/24131240_10210304380259338_4733926116983322399_n.jpg?oh=3b5e3c402bed835ee4d1513112e4d86b&oe=5ABDBE45'
        assert avatar[0:len(expected)] == expected

    def test_make_unique_nickname(self):
        u = User(nickname='john', email='john@example.com')
        db.session.add(u)
        db.session.commit()
        nickname = User.make_unique_nickname('john')
        assert nickname != 'john'
        u = User(nickname = nickname, email = 'susan@example.com')
        db.session.add(u)
        db.session.commit()
        nickname2 = User.make_unique_nickname('john')
        assert nickname2 != 'john'
        assert nickname2 != nickname
        nickname = User.make_unique_nickname('susan')
        assert nickname == 'susan'

    def test_follow(self):
        u1 = User(nickname='John', email='john@example.com')
        u2 = User(nickname='Susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        assert u1.unfollow(u2) is None
        u = u1.follow(u2)
        db.session.add(u)
        db.session.commit()
        assert u1.follow(u2) is None
        assert u1.is_following(u2)
        assert u1.followed.count() == 1
        assert u1.followed.first().nickname == 'Susan'
        assert u2.followers.count() == 1
        assert u2.followers.first().nickname == 'John'
        u = u1.unfollow(u2)
        db.session.add(u)
        db.session.commit()
        assert not u1.is_following(u2)
        assert u1.followed.count() == 0
        assert u2.followers.count() == 0

    def test_follow_posts(self):
        # make four users
        u1 = User(nickname='john', email='john@example.com')
        u2 = User(nickname='susan', email='susan@example.com')
        u3 = User(nickname='mary', email='mary@example.com')
        u4 = User(nickname='david', email='david@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        # make four posts
        utcnow = datetime.utcnow()
        p1 = Post(body="post from john", author=u1, timestamp=utcnow + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2, timestamp=utcnow + timedelta(seconds=2))
        p3 = Post(body="post from mary", author=u3, timestamp=utcnow + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4, timestamp=utcnow + timedelta(seconds=4))
        db.session.add(p1)
        db.session.add(p2)
        db.session.add(p3)
        db.session.add(p4)
        db.session.commit()
        # setup the followers
        u1.follow(u1)  # john follows himself
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u2)  # susan follows herself
        u2.follow(u3)  # susan follows mary
        u3.follow(u3)  # mary follows herself
        u3.follow(u4)  # mary follows david
        u4.follow(u4)  # david follows himself
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        db.session.commit()
        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        assert len(f1) == 3
        assert len(f2) == 2
        assert len(f3) == 2
        assert len(f4) == 1
        assert f1 == [p4, p2, p1]
        assert f2 == [p3, p2]
        assert f3 == [p4, p3]
        assert f4 == [p4]

    def test_transation_check(self):
        # Making sure that the translation service is working properly
        assert translate_text('es', 'Hello') == 'Hola'

    def test_user(self):
        # Make valid nicknames
        n = User.make_unique_nickname('John_123')
        assert n == 'John_123'
        n = User.make_unique_nickname('John_123\n')
        assert n == 'John_123'
        # Create a new user
        u = User(nickname='john', email='john@example.com')
        db.session.add(u)
        db.session.commit()
        assert u.is_authenticated is True
        assert u.is_active is True
        assert u.is_anonymous is False
        assert u.id == int(u.get_id())

# Coverage initializer
if __name__ == '__main__':
    try:
        unittest.main(verbosity=3)
    except:
        pass
    cov.stop()
    cov.save()
    print("\n\nCoverage Report:\n")
    cov.report()
    print("HTML Version: " + os.path.join(basedir, "tmp/coverage/index.html"))
    cov.html_report(directory='tmp/coverage')
    cov.erase()