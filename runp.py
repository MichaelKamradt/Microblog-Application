# !Flask/scripts/python
# Running this without debug mode on (production mode)
from app import app
app.run(debug=False) # Imports the app variable and runs the server