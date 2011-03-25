# Imports
import os
import cgi
import datetime
from presentation import Presentation     # Presentation data model

# Web App Stuff
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from django.utils import simplejson

# Handles the registration page
# Will create or remove listening sessions
class RegisterHandler(webapp.RequestHandler):

  # Retreives details on a presentation
  # If it exists
  def get(self, pptId):
    # Attempt to find the key
    key = db.Key.from_path('Presentation',int(pptId))               # find the key if it exists, must convert pptId to integer
    presentation = db.get(key)
    if (presentation == None):
      self.error(404)                                               # doesn't exist, out of luck send the 404
    else:
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps(presentation.ToDictionary()))

  # Requests a new presentation id to be generated 
  # the secondary parameter is unused since we are retreving a new registration id
  # It isn't required in the URL but appengine complains if our method doesn't accept two params
  def post(self,unused):
    # Get the post parameters and ensure they are valid
    name = self.request.get('name')                                 # Name of presentation
    num_slides = self.request.get('slides')                         # Number of slides

    if (name == '' or not num_slides.isdigit()):                       # If the parameters aren't correct then let them know
      self.error(500)
      self.response.out.write("The post parameters 'name' and 'slides' are required.  'slides' must also be a number\n")
    else:
      p = Presentation(Name=name, NumberSlides=int(num_slides))     # Create a new presentation
      p.put()                                                       # creates a default basic presentation
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({"id": p.key().id()})) # Send out the json id

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
      actions = presentation.PopAllActions()                        # Get the actions
      presentation.put()

      # We convert the actions to a list so it can easily be handled in javascript
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({"Actions": actions})) # Send out the json id

  # Posts a new action for this id
  # This will be a one-off request made by an android app or something
  def post(self, pptId):
    # Just makes it a bit easier to throw an error
    # This is local so it can't be used elsewhere
    def throwError(msg):                                            
      self.error(500)
      self.response.out.write(msg + '\n')

    # Find the presentation and set its actions
    key = db.Key.from_path('Presentation',int(pptId))               # find the key if it exists, must convert pptId to integer
    presentation = db.get(key)
    if (presentation == None):
      self.error(404)                                               # doesn't exist, out of luck send the 404
    else:
      self.response.set_status(204)                                 # Assuming everything ends up okay, we will set the status to 204 to indicate no content but sucess

      action = self.request.get('action').lower()                   # Get the action and calls the appropriate method
      if action == 'prev':  
        presentation.PushPreviousAction()
        presentation.put()
      elif action == 'next':
        presentation.PushNextAction()
        presentation.put()
      elif action == 'first':
        presentation.PushFirstAction()
        presentation.put()
      elif action == 'last':
        presentation.PushLastAction()
        presentation.put()
      elif action == 'goto':                                        # Goto is a little more complicated
        slide = self.request.get('slide')                           # They must give us a slide
        if not slide.isdigit():                                     # If its not a digit throw an error
          throwError("Goto action requires the 'slide' parameter which must be a number")
        else:
          try:
            presentation.PushGotoAction(int(slide))                 # we try to push this slide as the goto action
            presentation.put()
          except IndexError:                                        # this will occur if its greater than the number of slides
            throwError("Invalid slide number, it must be less than the maximum number of slides")
      else:                                                         # This occures if the its not one of the prespecified actions
        throwError("Invalid action, must be prev, next, first, last, or goto")

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
