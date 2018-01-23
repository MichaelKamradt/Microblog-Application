# python script used to bipass command line prompts by using the API

import imp
from migrate.versioning import api
from app import db
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO

v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migrate.py' % (v + 1)) # Incrememt the versions

tmp_module = imp.new_module('old_model') # Create a temporary model based on the old model  
old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO) # Creates a new version by comparing the old and the new

exec(old_model, tmp_module.__dict__) 

script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, tmp_module.meta, db.metadata) # Make an update for the script

open(migration, "wt").write(script)

api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO) # Update the current repo with the new updates

v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO) # Get the new version of the api

print('New migration saved as: ' + migration)
print('Current database version: ' + str(v))

# Always run in development before production
# Make sure you always have a back-up database before making migrations