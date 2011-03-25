# Imports
import os
import cgi
import datetime
import Queue

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
  def post(self,unused):
    # Create a new presentation and return the key
    p = Presentation()
    p.put()                                                         # creates a default basic presentation
    self.response.out.write(p.key().id())                           # Writes just the id of the key so fanciness required

  # Deletes a session id if exists
  # This will signify the end of a session
  def delete(self,pptId):
    key = db.Key.from_path('Presentation',int(pptId))               # Get the key from the pptId (which we convert to integer)
    presentation = db.get(key)
    if (presentation == None):                                      # If it doesn't exist
      self.error(404)                                               # we do a 404
    else:
      presentation.delete()                                         
      self.response.set_status(204)                                 # Otherwise, we delete it and send a 204 code which means no content 
    

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
      # Print the template
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write("present: ")
      self.response.out.write(pptId)
      self.response.out.write("\ncreated: ")
      self.response.out.write(presentation.DateCreated)

  # Puts a new event for this id
  # This will be a one-off request made by an android app or something
  def put(self, pptId):
    key = db.Key.from_path('Presentation',int(pptId))               # find the key if it exists, must convert pptId to integer
    presentation = db.get(key)
    if (presentation == None):
      self.error(404)                                               # doesn't exist, out of luck send the 404
    else:
      self.response.set_status(204)                                 # No Content is sent so we send a 204 to indicate success

# Models a presentation
class Presentation(db.Model):
  DateCreated = db.DateTimeProperty(auto_now_add = True)   	# The date/time this presentation was created
  NumberSlides = db.IntegerProperty()						# Number of slides in this presentation
  Name = db.StringProperty()								# Name of presentation  
  # Each Action is in the form of G Action
  # IE: Previous is GP, Next is GN, First is G1, Last is GE, and any number is G##
  Actions = db.StringProperty()								# For simplicity we are using the string as an action storage method this is at least for now
  
  # Pushes a previous action onto the action list
  # If preceded by a next action, the next action is removed and this action is ignored
  def PushPreviousAction():	    
    if (Actions.count('G') > 1 and Actions[-2:] == "GN"):
	    Actions = Actions[:-2]	   
    else:	   
        Actions += "GP"
	
  # Pushes a next action onto the action list
  # If preceded by a previous action, the previous action is removed and this action is ignored
  def PushNextAction():
    if (Actions.count('G') > 1 and Actions[-2:] == "GP"):
	    Actions = Actions[:-2]	    
	else:
	    Actions += "GN"
	
  # Pushes a first action onto the action list
  # Will remove all actions in the action list
  def PushFirstAction():
     Actions = "G1"
	
  # Pushes an end action onto the action list
  # Will remove all actions in the action list
  def PushLastAction():
     Actions = "G" + NumberSlides
	
  # Pushs a goto action onto the action list
  # Will remove all actions in the action list
  def PushGotoAction(slide_num):
    if (slide_num > NumberSlides || slide_num < 1):
		raise IndexError("Slide Number Is Invalid")
	Actions = "G" + slide_num
  
  # PopAllActions
  # Returns the current action string
  # Then sets it to ''.  
  # The idea being the presentation long-poller will retrieve all actions to perform at once
  # TODO: Sometime we'll have to deal with the concurrency issues that will inevitabbly pop up
  def PopAllActions():
    t = Actions
    Actions = ''
	return t
  

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
