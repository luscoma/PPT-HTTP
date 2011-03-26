# Represents the presentation data model
# This model has a couple of neat methods for pushing and popping 
# Presentation actions

# Date Time
import datetime

# Web App Stuff
from google.appengine.ext import db

# Models a presentation
class Presentation(db.Model):
  DateCreated = db.DateTimeProperty(auto_now_add = True)       # The date/time this presentation was created
  NumberSlides = db.IntegerProperty()                          # Number of slides in this presentation
  Name = db.StringProperty()                                   # Name of presentation  
  # Each Action is in the form of G Action
  # IE: Previous is GP, Next is GN, First is G1, Last is GE, and any number is G##
  Actions = db.StringProperty('')                              # For simplicity we are using the string as an action storage method this is at least for now
  Token = db.StringProperty()                                  # The token to identify the client id
  LastHeartBeat = db.DateTimeProperty(auto_now_add = True)     # The date/time this presentation last received a heart beat

  # Make sure actions is initialized
  def __checkAction(self):
    if self.Actions == None:
      self.Actions = ''

  # Pushes a previous action onto the action list
  # If preceded by a next action, the next action is removed and this action is ignored
  def PushPreviousAction(self):        
    self.__checkAction()
    if (self.Actions.count('G') > 0 and self.Actions[-2:] == "GN"):
      self.Actions = self.Actions[:-2]       
    elif self.Token:            # If theres a token they don't need a list of actions, it will be sent over the channel instantly
      self.Actions = "GP"
    else:                       # Otherwise, we append since they will be using the standard pop interface
      self.Actions += "GP"
    
  # Pushes a next action onto the action list
  # If preceded by a previous action, the previous action is removed and this action is ignored
  def PushNextAction(self):
    self.__checkAction()
    if (self.Actions.count('G') > 0 and self.Actions[-2:] == "GP"):
      self.Actions = self.Actions[:-2]        
    elif self.Token:
      self.Actions = "GN"     # If theres a token, it will be sent instantly so no need to append
    else:
      self.Actions += "GN"    # Otherwise, we append since they will be using the standard pop interface
    
  # Pushes a first action onto the action list
  # Will remove all actions in the action list
  def PushFirstAction(self):
    self.__checkAction()
    self.Actions = "G1"
    
  # Pushes an end action onto the action list
  # Will remove all actions in the action list
  def PushLastAction(self):
    self.__checkAction()
    self.Actions = "G" + str(self.NumberSlides)
    
  # Pushs a goto action onto the action list
  # Will remove all actions in the action list
  def PushGotoAction(self,slide_num):
    self.__checkAction()
    if (slide_num > self.NumberSlides or slide_num < 1):
        raise IndexError("Slide Number Is Invalid")
    self.Actions = "G" + str(slide_num)
  
  # PopAllActions
  # Returns the current action string
  # Then sets it to ''.  
  # The idea being the presentation long-poller will retrieve all actions to perform at once
  # TODO: Sometime we'll have to deal with the concurrency issues that will inevitabbly pop up
  def PopAllActions(self):
    t = self.Actions or ''
    self.Actions = ''
    return t
  
  def ToDictionary(self):
    return {"Name": self.Name, "NumberSlides": self.NumberSlides, "DateCreated": self.DateCreated.strftime("%m/%d/%Y %H:%M"), "Actions": self.Actions}
