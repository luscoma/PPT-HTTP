# Imports
import os
import cgi
import datetime
from presentation import Presentation     # Presentation data model

# Web App Stuff
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# Handles the registration page
# Will create or remove listening sessions
class RegisterHandler(webapp.RequestHandler):

  # Gets a new session id generated for 
  # Use and types it
  # the secondary parameter is unused since we are retreving a new registration id
  # It isn't required in the URL but it appengine complains if our method doesn't accept two params
  def post(self,unused):
    # Get the post parameters and ensure they are valid
    name = self.request.get('name')                                 # Name of presentation
    num_slides = self.request.get('slides')                         # Number of slides

    if (name == '' or not num_slides.isdigit()):                       # If the parameters aren't correct then let them know
      self.error(500)
      self.response.out.write("The post parameters 'name' and 'slides' are required.  'slides' must also be a number\n")
    else:
      p = Presentation(Name=name, NumberSlides=int(num_slides))          # Create a new presentation
      p.put()                                                       # creates a default basic presentation
      self.response.out.write(p.key().id())                         # Writes just the id of the key, no fanciness required

  # Deletes a session id if exists
  # This will signify the end of a session
  def delete(self,pptId):
    key = db.Key.from_path('Presentation',int(pptId))               # Get the key from the pptId (which we convert to integer, which we know is an integer due to the regex)
    presentation = db.get(key)                                      # Retreive presentation
    if (presentation == None):                                      # If it doesn't exist
      self.error(404)                                               # we do a 404
    else:
      presentation.delete()                                         # Delete the presentation
      self.response.set_status(204)                                 # Send a 204 code which means ok, but no content
    

# Handles the present page
# Will retrieve or put new ppt events for a given id
class PresentHandler(webapp.RequestHandler):
  # Retreives any outstanding events for this id
  # Ideally will be long polled
  def get(self, pptId):
    # Attempt to find the key
    key = db.Key.from_path('Presentation',int(pptId))               # find the key if it exists, must convert pptId to integer
    presentation = db.get(key)
    if (presentation == None):
      self.error(404)                                               # doesn't exist, out of luck send the 404
    else:
      # Print the template (for now just debug)
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write("Present: ")
      self.response.out.write(pptId)
      self.response.out.write("\nCreated: ")
      self.response.out.write(presentation.DateCreated)
      self.response.out.write("\nName: ")
      self.response.out.write(presentation.Name)
      self.response.out.write("\nSlides: ")
      self.response.out.write(presentation.NumberSlides)
      self.response.out.write("\nAction: ")
      self.response.out.write(presentation.Actions)

  # Puts a new event for this id
  # This will be a one-off request made by an android app or something
  def put(self, pptId):
    key = db.Key.from_path('Presentation',int(pptId))               # find the key if it exists, must convert pptId to integer
    presentation = db.get(key)
    if (presentation == None):
      self.error(404)                                               # doesn't exist, out of luck send the 404
    else:
      self.response.set_status(204)                                 # No Content is sent so we send a 204 to indicate success

# Application Object
application = webapp.WSGIApplication( 
                          [
                            ('/service/register(?:/(\d+))?', RegisterHandler),
                            ('/service/present/(\d+)', PresentHandler),
                          ]
                          ,debug=True)

# Main Application
def main():
  run_wsgi_app(application)
if __name__ == "__main__":
  main()
