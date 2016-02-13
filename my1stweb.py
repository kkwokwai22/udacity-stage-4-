import urllib
import urllib2
import webapp2

from google.appengine.ext import db
from google.appengine.api import users

import jinja2
import os


template_directory = os.path.join(os.path.dirname(__file__), 'html_templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_directory),
	autoescape = True)

class Greeting(db.Model):
  """Models an individual Guestbook entry with an author, content, and date."""
  author = db.StringProperty()
  age = db.StringProperty()
  content = db.StringProperty(multiline=True, indexed=False)
  date = db.DateTimeProperty(auto_now_add=True)


def _GuestbookKey(guestbook_name=None):
  """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')


class MainPage(webapp2.RequestHandler):

  def get(self):  # pylint:disable-msg=invalid-name
    """Handle GET requests."""
    guestbook_name = self.request.get('guestbook_name')
    greetings_query = Greeting.all().ancestor(
        _GuestbookKey(guestbook_name)).order('-date')
    batch = 5
    greetings = greetings_query.fetch(batch)

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
        'greetings': greetings,
        'url': url,
        'url_linktext': url_linktext,
        'error': self.request.get('error')
    }

    template = jinja_env.get_template('content.html')
    self.response.out.write(template.render(template_values))


class Guestbook(webapp2.RequestHandler):

  def post(self):  # pylint:disable-msg=invalid-name
    """Handle POST requests."""
    # We set the same parent key on the 'Greeting' to ensure each greeting is in
    # the same entity group. Queries across the single entity group will be
    # consistent. However, the write rate to a single entity group should
    # be limited to ~1/second.
    guestbook_name = self.request.get('guestbook_name')
    greeting = Greeting(parent=_GuestbookKey(guestbook_name))

    if users.get_current_user():
      greeting.author = users.get_current_user().nickname()

    greeting.age = self.request.get('age')
    greeting.content = self.request.get('content')
    if greeting.content.strip() and greeting.age.isdigit():
      greeting.put()
      self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}) + '#comments')
    else:
      error = 'Enter text for comment and positive whole number for age.'
      self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name, 'error': error}) + '#comments')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
], debug=True)
