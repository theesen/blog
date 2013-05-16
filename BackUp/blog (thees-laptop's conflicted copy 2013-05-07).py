import webapp2
import jinja2
import os
from google.appengine.ext import db
from string import letters

import re

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

def render_post(response, post):
	response.out.write('<b>' + post.subject + '</b><br>')
	response.out.write(post.blog_post)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)
	
	def render(self, template, **kw):
		self.write(self.render_str(template,**kw))
		
def blog_key(name='default'):
	return db.Key.from_path('blogs', name)
	
class Post(db.Model):
	blog_title = db.StringProperty(required = True)
	blog_post = db.TextProperty(required = True)
	date_published = db.DateTimeProperty(auto_now_add = True)
	
	def render(self):
		self._render_text = self.blog_post.replace('\n','<br>')
		return render_str('permalink.html', p = self)

class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts)
		
class Main(Handler):
	def get(self):
		posts = db.GqlQuery('SELECT * FROM Post ORDER BY date_published DESC limit 10')
		self.render('front.html', posts=posts)
		
		
class PostPage(Handler):
	def get(self, post_id):
		key = db.Key.from_path('Post', int(post_id), parent=blog_key())
		post = db.get(key)
		
		if not post:
			self.error(404)
			return
		
		self.render('permalink.html', post = post)
	
class NewPost(Handler):
	def get(self):
		self.render('newpost.html')
		
	def post(self):
		blog_title = self.request.get('blog_title')
		blog_post = self.request.get('blog_post')
		
		if blog_title and blog_post:
			b = Post(parent = blog_key(), blog_title=blog_title, blog_post=blog_post)
			b.put()
			self.redirect('/%s' % str(b.key().id()))
		else:
			error = "Title and Post must be filled!"
			self.render('newpost.html', blog_title=blog_title, blog_post=blog_post, error=error)


app = webapp2.WSGIApplication([('/blog', Main),
								('/blog/newpost', NewPost),
								('/blog/?', BlogFront),
								('/blog/([0-9]+)', PostPage),
								], 
								debug = True)
