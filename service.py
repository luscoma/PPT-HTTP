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
    enable_channel = self.request.get('channel')                    # Channel enables the use of the channel API

    if (name == '' or not num_slides.isdigit()):                       # If the parameters aren't correct then let them know
      self.error(500)
      self.response.out.write("The post parameters 'name' and 'slides' are required.  'slides' must also be a number\n")
    else:
      p = Presentation(Name=name, NumberSlides=int(num_slides))     # Create a new presentation
      p.put()                                                       # creates a default basic presentation

      if enable_channel:                                            # if channel is provided at all, then we create a channel token and update the data structure
        p.Token = channel.create_channel(str(p.key().id()));    
        p.put()

      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({"id": p.key().id(), "token": p.Token})) # Send out the json id and optional channel token

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
    result = db.run_in_transaction(self.__transactionPopAll, pptId)   # We run this in a transaction (so noone adds a command while we're popping)
    if not result[0]:                                                 # Did it fail?
      self.error(404)                                                 # Couldn't find it so we error
    else:                                                             # Else we convert the action string to JSON
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({"Actions": result[1]})) # Send out the json string of actions

  # Pops all actions out of the presentation item
  # In an atomic transaction, this way we don't have to worry about 
  # Someone adding things to the presentation while we work
  def __transactionPopAll(self, pptId):
    key = db.Key.from_path('Presentation',int(pptId))             # find the key if it exists, we must convert pptId to an integer
    presentation = db.get(key)
    if presentation == None:
      return (False, None)
    
    actions = presentation.PopAllActions() or ''                  # Pop all the transactions and recommit this item to the database
    presentation.put()
    return (True, actions)                                        # we return the actions we popped off

  # Posts a new action for this id
  # This will be a one-off request made by an android app or something
  def post(self, pptId):
    # Get the required post parameters
    action = self.request.get('action').lower()
    slide = self.request.get('slide')

    # Check if this is a valid action
    try:
      if action == "goto" and not slide.isdigit():                # Do a specific check for the goto command to ensure the slide value is a digit
        self.error(500)
        self.response.out.write("Goto action requires the 'slide' parameter which must be a number\n")
      else:
        result = db.run_in_transaction(self.__transactionPushAction, pptId, action, slide)
        if not result[0]:                                         # if result is false, we return 404
          self.error(404)
        else:
          self.response.set_status(204)                           # Assuming everything ends up okay, we will set the status to 204 to indicate no content but sucess

          # Check for channel
          if result[2]:                                           # If the token parameter isn't null or '' then lets push out to the token
            channel.send_message(pptId, simplejson.dumps({ "Actions": result[1] }))
    except ValueError:
      self.error(500)
      self.response.out.write("Invalid action, must be prev, next, first, last, or goto")
    except IndexError:                                        
      self.error(500)
      self.response.out.write("Invalid slide number, it must be less than the maximum number of slides")

  # Pushes an action atomically onto a presentation
  # action and slide are the request parameters, slide is only required when action goto
  # returns False if key wasn't found, true if we succeeded also the channel token and current actions so we don't have to re-request this item from the db
  def __transactionPushAction(self, pptId, action, slide):
    key = db.Key.from_path('Presentation',int(pptId))               # find the key if it exists, must convert pptId to integer
    presentation = db.get(key)                                      # find the presentation
    if (presentation == None):                                      # doesn't exist return False
      return (False)

    # Find the proper action
    if action == 'prev':                                            
      presentation.PushPreviousAction()
    elif action == 'next':
      presentation.PushNextAction()
    elif action == 'first':
      presentation.PushFirstAction()
    elif action == 'last':
      presentation.PushLastAction()
    elif action == 'goto':                                        
      presentation.PushGotoAction(int(slide))                       # We try to push this slide as the goto action
    else:
      raise ValueError("Action Invalid")                            # Throw a value error to indicate an invalid action

    # Do a final check, are we going to be using a channel to submit data?
    # If so we should clear the action list, maybe ultimately we can just only use channels
    # But for now we will support both since the channel API only works in javascript
    actions = presentation.Actions
    if presentation.Token:
      presentation.Actions = ''
    presentation.put()                                              # Commit the changes
    return (True, actions, presentation.Token)                      # return True to indicate we did something successfully

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
