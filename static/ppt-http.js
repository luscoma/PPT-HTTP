/*
 * Presentation Service Class
 *
 * Easy to interact with javascript class which wraps
 * the ppt-http service.  Does not implement the channel api
 * that is implemented separately.
 */

// Namespace for this object is PPTHTTP
PPTHTTP = {};

// Actual Fun Stuff
(function() {
  
  // URL Local Stuff
  //var URL = "http://ppt-http.appspot.com";
  var URL = "http://localhost:8080";
  function MakeURL(cmd, id)
  {
    if (id === undefined) 
      return URL + "/service/" + cmd; 
    return URL + "/service/" + cmd + "/" + id;
  }

  this.Service = function() {
    this.Id = 0;
    this.Token = null;
  }
  // Processes a heart beat
  this.Service.prototype.heartbeat = function() 
  { 
    // the way this will work is simple
    // we should just make a simple request to /service/heartbeat to say were here
    // In the future stuffl ike this will all have to be jsonp but whatever for now
    $.get(MakeURL("heartbeat",this.Id));
  }
  // Parses a list of actions and calls the appropriate functions
  this.Service.prototype.parse = function(actions) {
    // defined a utility function which checks for integer
    function isInt(x) {
      var y=parseInt(x); 
      if (isNaN(y)) return false; 
      return x==y && x.toString()==y.toString(); 
    }

    // Split and loop through the actions
    me = this;  // each overrides this, so we store the current this as me              
    console.log(actions);
    var split_actions = actions.split('G').splice(1);
    $.each(split_actions, function(idx, cmd)
    {
      if (cmd == "N" && $.isFunction(me.onNext)) {  me.onNext(); }
      else if (cmd == "P" && $.isFunction(me.onPrev)) {  me.onPrev(); }
      else if (isInt(cmd) && $.isFunction(me.onGoto)) { me.onGoto(parseInt(cmd)); }
    });
  }
  this.Service.prototype.delete = function() {
      $.ajax({
        url: MakeURL("register",this.Id),
        type: "DELETE",
        success: function(data) { clearInterval(this._hb); },
        context: service,
      });
  }


  // Registers a presentation with the service
  // Returns a service object containing the stuff
  this.register = function(name, slides) {
      var service = new this.Service();
      service.Name = name;
      service.Slides = slides;

      $.ajax({
        url: MakeURL("register"),
        type: "POST",
        dataType: "json",
        data: "name=" + name + "&slides=" + slides + "&channel=true", // ideally i'd like to use JSON, but we can't really do that right now, i'd like to see it work first
        error: function() {
          alert("Well that failed");
        },
        success: function(data) {
          this.Id = data.id;
          this.Token = data.token;

          // Initialize Channel
          me = this;
          this.Channel = new goog.appengine.Channel(this.Token);
          this.Socket = this.Channel.open();
          this.Socket.onopen = function() { console.log("opened"); };
          this.Socket.onmessage = function(message) { me.parse(JSON.parse(message.data).Actions); };

          // HeartBeat
          this._hb = setInterval(function() { me.heartbeat(); }, 30000);
        },
        context: service,
      });

      return service;
  };
 }).call(PPTHTTP)
