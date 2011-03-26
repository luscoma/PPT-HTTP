# Imports
import os
import cgi
import datetime
from presentation import Presentation     # Presentation data model

# Web App Stuff
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import channel
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

      token = channel.create_channel(str(p.key().id()));              

      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({"id": p.key().id(), "token": token})) # Send out the json id and optional channel token

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

  # Posts a new action for this id
  # This will be a one-off request made by an android app or something
  def post(self, pptId):
    # Easy to use error function
    def throwError(msg):
      self.error(500)
      self.response.out.write(msg + "\n")

    # Get the required post parameters
    action = self.request.get('action').lower()
    slide = self.request.get('slide')

    # Get the presentation
    key = db.Key.from_path('Presentation',int(pptId))               # find the key if it exists, must convert pptId to integer
    presentation = db.get(key)                                      # find the presentation
    if (presentation == None):                                      # doesn't exist return False
      self.error(404)                                               # 404 Error
      return

    # Validate action so we can send it through the channel
    if action == 'prev':                                            
      channel.send_message(pptId, simplejson.dumps({ "Action": "GP" }))     # Send the previous command
    elif action == 'next':
      channel.send_message(pptId, simplejson.dumps({ "Action": "GN" }))     # Send the next command
    elif action == 'first':
      channel.send_message(pptId, simplejson.dumps({ "Action": "G1" }))     # Send the Goto Slide 1 command
    elif action == 'last':
      cmd = "G" + str(presentation.NumberSlides)
      channel.send_message(pptId, simplejson.dumps({ "Action": cmd }))      # Send the goto Slide (Last) command
    elif action == 'goto':                                        
      if not slide.isdigit():                                               # check if the slide # specified is valid
        throwError("Goto action requires the 'slide' parameter which must be a number")
        return
      elif int(slide) > presentation.NumberSlides or int(slide) < 1:        # check if its within the presentation bounds
        throwError("Invalid slide number specified")
        return
      else:
        cmd = "G" + slide                                                   # Send the goto # message
        channel.send_message(pptId, simplejson.dumps({ "Action": cmd }))
    else:
      throwError("Invalid action, must be prev, next, first, last, or goto")  # Invalid Action occurred
      return

    self.response.set_status(204)                           # Assuming everything ends up okay, we will set the status to 204 to indicate no content but sucess

# Manages a heartbeat for an application
class HeartbeatHandler(webapp.RequestHandler):
  # Updates the heartbeat
  def get(self, pptId):
    key = db.Key.from_path('Presentation',int(pptId))
    presentation = db.get(key)
    if (presentation == None):
      self.error(404)
    else:
      presentation.HeartBeat = datetime.datetime.utcnow()
      presentation.put()
      self.response.set_status(204)

# Application Object
application = webapp.WSGIApplication( 
                          [
                            ('/service/register(?:/(\d+))?', RegisterHandler),
                            ('/service/present/(\d+)', PresentHandler),
                            ('/service/heartbeat/(\d+)', HeartbeatHandler)
                          ]
                          ,debug=True)

# Main Application
def main():
  run_wsgi_app(application)
if __name__ == "__main__":
  main()
