# Imports
import os
import cgi

# Web App Stuff
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

# Main Page Handler
class IndexHandler(webapp.RequestHandler):

  def get(self):
    # Print the template
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, None))

# Application Object
application = webapp.WSGIApplication([('/(?:index)?', IndexHandler)],debug=True)

# Main Application
def main():
  run_wsgi_app(application)
if __name__ == "__main__":
  main()
