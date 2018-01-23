import json

from rauth import OAuth2Service
from flask import url_for, request, redirect, session
from app import app
from .models import User

class OAuthSignIn(object):
    providers = None

    # Initializes the process
    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    # Sends the user to the provider's website to handle the authentication
    def authorize(self):
        pass

    # Calls back to the app
    def callback(self):
        pass    

    # Built using the provider's name, so each provider gets its own path
    def get_callback_url(self):
        return url_for('oauth_callback', provider = self.provider_name, _external = True)
    
    # Made to look up the correct provider instance given the name
    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class FacebookOAuthSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookOAuthSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name = 'facebook',
            client_id = self.consumer_id,
            client_secret = self.consumer_secret,
            authorize_url = 'https://graph.facebook.com/oauth/authorize',
            access_token_url = 'https://graph.facebook.com/oauth/access_token',
            base_url = 'https://graph.facebook.com/'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope = 'email',
            response_type = 'code',
            redirect_uri = self.get_callback_url()
    ))

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data = {'code': request.args['code'],
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.get_callback_url()},
            decoder = decode_json
        )
        me = oauth_session.get('me').json()
        return (
            'facebook$' + me['id'],
            me['name'], # Facebook does not provide username, so the email's user is used instead
            me.get('email')
    )