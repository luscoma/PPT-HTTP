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
  LastHeartBeat = db.DateTimeProperty(auto_now_add = True)     # The date/time this presentation last received a heart beat
  
  def ToDictionary(self):
    return {"Name": self.Name, "NumberSlides": self.NumberSlides, "DateCreated": self.DateCreated.strftime("%m/%d/%Y %H:%M") }
