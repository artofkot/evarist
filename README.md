i think we should sum up changes we make with each commit somewhere for each other.
i dunno, how it's supposed to be done, but i added this readme and stored changes and comments here under the header same as the -m in commit


###### add Blueprints
	- add to listki.py this stuff
	app = Flask('listki')
	app.register_blueprint(flaskr)

	...

	mongo = PyMongo(app)
	@app.before_request
	def before_request():
    	g.mongo = mongo

	- moved all flaskr controllers to flaskr.py, and add this there
	flaskr = Blueprint('flaskr', __name__,
                    template_folder='templates')

    - minor changes to controllers and html files so that it all works
    (such as g.mongo instead of mongo, flakr.show_entries.html instead of show_entries.html)

    - for detailes see the commit


###### add bootstrap and MERGE
	- add static/vendor   - a place for all third party plugins, libs and such (such as bootstrap)
	- add vendor/bootstrap  (note, that this is actually not used in code, instead we use CDN)
	- add bootstrap-specific headers to <head> of layout.html
	- add bootstrap CDN links to <head> of layout.html (cmd+F TOREAD)
	- add startertry.html to play with bootstrap  +  add app.startertry() to listki.py
	- add starter-template.css (see comment in layout.html) 
		an important thing. although bootstrap is cool, if you want to use it you still need to modify htmls and custom css's so that everything works fine. for example, if youb want to add navbar, you need to add what's in starter-template.css. 
	- add navbar (copypaste from bootstrap example starter-template) to show_entries.html to test bootstrap further
	- well, now bootstrap works. next thing to do: modify templates so that they are compatible with bootstrap.
	- add README.md
	- rename <title> in layout to Listki