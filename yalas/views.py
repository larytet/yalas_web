import flask
import wtforms
import werkzeug
import os
import collections
import operator

import time
import forms

FlaskRoute = collections.namedtuple('FlaskRoute', ['route', 'name', 'cb', 'methods', 'index'], verbose=False)

class Views:
    
    def __init__(self, app):
        self.app = app
        self.add_routes(app)
        self.users = {}
    
    def add_routes(self, app):
        self.ROUTES = [
            FlaskRoute('/',                     'index',    self.index,         None,               True),
            FlaskRoute('/link',                 'link',     self.link,          None,               True),
            FlaskRoute('/search',               'search',   self.search,        ['GET', 'POST'],    True),
            FlaskRoute('/hello/',               'hello',    self.hello,         None,               True),
            FlaskRoute('/hello/<string:name>',  'hello',    self.hello,         None,               False),
            FlaskRoute('/upload',               'upload',   self.upload_file,   ['GET', 'POST'],    True),
            FlaskRoute('/login',                'login',    self.login,         ['GET', 'POST'],    True),
        ]
        for flask_route in self.ROUTES:
            methods = flask_route.methods 
            if methods is None:
                methods = ['GET']
            app.add_url_rule(flask_route.route, flask_route.name, flask_route.cb, methods=methods)
    
    def log_the_user_in(self, username):
        if not username in self.users:
            self.users[username] = {'time':time.clock(), 'searches':[], 'uploads': []}
                        
    def get_user_data(self, username):
        return self.users.get(username, None)

    def flash_user(self, request):
        username = request.cookies.get('username', None)
        if not username:
            flask.flash("Not logged in")
        else:
            userdata = self.get_user_data(username)
            if userdata:
                flask.flash("Logged in as '{0}':'{1}'".format(username, userdata))
            else:
                flask.flash("Unknown user '{0}'".format(username))
                
    def update_user(self, request, key, data):
        username = request.cookies.get('username', None)
        if username:
            userdata = self.get_user_data(username)
            if userdata:
                userdata[key].append(data)
                
    def update_user_searches(self, request, search_query):
        self.update_user(request, 'searches', search_query)
                
    def update_user_uploads(self, request, filename):
        self.update_user(request, 'uploads', filename)
        
    def link(self):
        url = flask.url_for('static', filename='style.css')
        return flask.render_template('url.html', name="style.css", url=url)
    
    def index(self):
        urls = []
        for flask_route in self.ROUTES:
            if flask_route.index:
                urls.append((flask_route.route, flask_route.name))
        urls.sort(key=operator.itemgetter(1))
        return flask.render_template('index.html', urls=urls)
    
    def hello(self, name=None):
        return flask.render_template('hello.html', name=name)
    
    # Security related feature- make sure that html, php&friends are not here
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    def allowed_file(self, filename):
        result = '.' in filename
        extension = None
        if result:
            extension = filename.rsplit('.', 1)[1].lower()
            result = extension in self.ALLOWED_EXTENSIONS
        return result, extension  
    
    def upload_file(self):
        request = flask.request
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flask.flash('No file part in the request')
                return flask.redirect(request.url)
            attr_file = request.files.get('file', None)
            
            if attr_file is None:
                flask.flash('No file attribute in the POST')
                return flask.redirect(request.url)
            
            # if user does not select file, browser also
            # submit a empty part without filename
            if attr_file.filename == '':
                flask.flash('No selected file')
                return flask.redirect(request.url)

            is_allowed, file_extension = self.allowed_file(attr_file.filename)
            if is_allowed:
                filename = werkzeug.utils.secure_filename(attr_file.filename)
                flask.flash('Uploaded {0} to {1}'.format(filename, self.app.config.upload_folder))
                attr_file.save(os.path.join(self.app.config.upload_folder, filename))
                self.update_user_uploads(request, filename)
                self.flash_user(request)
                return flask.redirect(flask.url_for('upload', filename=filename))
            else:
                flask.flash('File type {0} is not supported'.format(file_extension))
                return flask.redirect(request.url)

        return flask.render_template('upload.html') 
                    
    def search(self):
        request = flask.request
        search_form = forms.SearchForm(request.form)
    
        flask.flash("Form errors: {0}".format(search_form.errors))
        if request.method == 'POST':
            search_query = request.form['search']
            #flask.flash("Search query: {0}".format(search_query))
            if search_form.validate():
                # Save the comment here.
                flask.flash('Search ' + search_query)
                self.update_user_searches(request, search_query)
                self.flash_user(request)
            else:
                flask.flash("Got '{0}'. All the form fields are required. ".format(search_query))
     
        rsp = flask.make_response(flask.render_template('search.html', form=search_form))
        return rsp
    
    
    def login(self):
        request = flask.request
        login_form = forms.LoginForm(request.form)
        username = None
        if request.method == 'POST':
            username = request.form['username']
            flask.flash("Login: {0}".format(username))
            self.log_the_user_in(username)
            # the code below is executed if the request method
            # was GET or the credentials were invalid
        rsp = flask.make_response(flask.render_template('/login.html', form=login_form))
        if username:
            rsp.set_cookie("username", username)
        return rsp
