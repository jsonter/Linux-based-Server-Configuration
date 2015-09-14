'''
***********************************************************************
Developer: Justin Sonter (jsonter@gmail.com)

Udacity Full Stack Web Developer Nanodegree Project 3.

This project provides a list of items within a variety of categories.

***********************************************************************
The following extra Python packages are required for this application.

(pip install xxx)

Flask, SQLAlchemy, requests, httplib2, oauth2client.

***********************************************************************
'''
import os
import random
import string
import requests
import json
import httplib2

from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify, make_response
from flask import session as login_session

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

from werkzeug import secure_filename

from database_setup import Base, User, Category, Item

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/catalog/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

# Settings for picture uploads
UPLOAD_FOLDER = '/var/www/catalog/catalog/static/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Setting for default page behaviour
NUM_LAST_ITEMS = 5  # The number of items to show if no category is selected.

engine = create_engine('postgresql://catalog:fgRT56rkG@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    '''
    Decorator function to check if user is logged in.
    Apply this decorator to any function that requires user
    authentication.
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in login_session:
            return f(*args, **kwargs)
        else:
            flash('You are not logged in!')
            return redirect(url_for('catalog'))
    return decorated_function


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    ''' Function to authenticate with facebook. '''
    # Validate the state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Get the short-term access token
    access_token = request.data

    # Get the long-term access token from facebook using the short-term token.
    app_id = json.loads(open('/var/www/catalog/catalog/fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('/var/www/catalog/catalog/fb_client_secrets.json', 'r').read())['web']['app_secret']

    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.2/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    # Get the users info from facebook using long-term token.
    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    # so let's strip out the information before the equals sign in our token.
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # See if user exists, if it doesn't; make a new one.
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    # If user found, add the user id to the session.
    # If new user cannot be added, disconnect the facebook account.
    if user_id:
        login_session['user_id'] = user_id
    else:
        return redirect(url_for('fbdisconnect'))

    return redirect(url_for('catalog'))


@app.route('/fbdisconnect')
def fbdisconnect():
    ''' Function to disconnect from facebook '''
    facebook_id = login_session['facebook_id']
    # The access token must be included to successfully logout
    access_token = login_session['access_token']

    url = 'https://graph.facebook.com/%s/permissions?fb_exchange_token=%s' % \
        (facebook_id, access_token)

    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    ''' Function to authenticate with Google Plus. '''
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/catalog/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't; make a new one.
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    # If user found, add the user id to the session.
    # If new user cannot be added, disconnect the google account.
    if user_id:
        login_session['user_id'] = user_id
    else:
        return redirect(url_for('gdisconnect'))

    return redirect(url_for('catalog'))


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    ''' Function to disconnect from Google. '''
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['credentials']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    '''
    Function to disconnect user from whichever authentication provider
    they are using.
    '''

    if 'provider' in login_session:
        # Disconnect based on provider
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('catalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('catalog'))


@app.route('/')
@app.route('/catalog')
@app.route('/category/<int:category_id>')
def catalog(category_id=0):
    '''
    Base url function.
    Show list of all categories and latest (5) items for any category.
    If url is /category/<int:category_id> then limit items to that
    category only.
    '''

    # Generate state variable for login token exchange.
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for
                    x in xrange(32))

    login_session['state'] = state
    categories = session.query(Category).order_by(Category.name)
    if category_id:
        # If category id is passed in, limit items to that category only.
        category = session.query(Category).filter_by(id=category_id).one()
        items = session.query(Item).filter_by(category_id=category_id)

    else:
        # No category, show latest 5 items.
        category = ''
        items = session.query(Item).order_by(Item.id.desc()).limit(
            NUM_LAST_ITEMS)

    if 'user_id' in login_session:
        # If user is logged in, pass user to template to show their
        # login details and CRUD options.
        user = getUserInfo(login_session['user_id'])
        return render_template(
            'catalog.html', user=user, categories=categories,
            category=category, items=items, STATE=login_session["state"])

    else:
        # If user is not logged in, template will only display
        # categories and items, no CRUD.
        return render_template(
            'catalog.html', user='', categories=categories,
            category=category, items=items, STATE=login_session['state'])


@app.route('/catalog.json')
def catalogJSON(category_id=False):
    '''
    JSON endpoint for database. All categories and their related items.
    '''
    categories = session.query(Category).all()
    serializedCategories = []
    for i in categories:
        # For each category, serialize it's data then append it's
        # serialized items.
        newCategory = i.serialize
        items = session.query(Item).filter_by(category_id=i.id).all()
        serializedItems = []
        for j in items:
            serializedItems.append(j.serialize)
        newCategory['items'] = serializedItems
        serializedCategories.append(newCategory)
    return jsonify(categories=[serializedCategories])


@app.route('/category/new', methods=['GET', 'POST'])
@login_required
def newCategory():
    '''
    Display new category template and save the entered category.
    '''
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['category'],
            user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash('New category created!')
        return redirect(url_for('catalog'))
    else:
        user = getUserInfo(login_session['user_id'])
        return render_template('newCategory.html', user=user)


@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    '''
    Display edit category template and save the selected category.
    '''
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except:
        flash("That category does not exist!")
        return redirect(url_for('catalog'))

    if request.method == 'POST':
        category.name = request.form['category']
        session.commit()
        flash("Category name changed!")
        return redirect(url_for('catalog'))
    else:
        # Only edit if category belongs to user, otherwise redirect.
        if category.user_id == login_session['user_id']:
            user = getUserInfo(login_session['user_id'])
            return render_template(
                'editCategory.html', user=user, category=category)
        else:
            flash("You may not edit a category that does not belong to you!")
            return redirect(url_for('catalog'))


@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    '''
    Display delete category template and delete the selected category.
    '''
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except:
        flash("That category does not exist!")
        return redirect(url_for('catalog'))

    if request.method == 'POST':
        # Deleting a category will cascade delete items in that category.
        # First remove any stored images for category images.
        removeCategoryPictures(category_id)
        session.delete(category)
        session.commit()
        flash("Category deleted!")
        return redirect(url_for('catalog'))
    else:
        # Only delete if category belongs to user, otherwise redirect.
        if category.user_id == login_session['user_id']:
            user = getUserInfo(login_session['user_id'])
            return render_template(
                'deleteCategory.html', user=user, category=category)
        else:
            flash("You may not delete a category that does not belong to you!")
            return redirect(url_for('catalog'))


@app.route('/category/<int:category_id>/<int:item_id>')
def showItem(category_id, item_id):
    '''
    Display the show item template, if user logged in and is the
    owner of the item; show the CRUD options.
    '''
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except:
        flash("That item does not exist!")
        return redirect(url_for('catalog'))

    if 'user_id' in login_session:
        user = getUserInfo(login_session['user_id'])
        return render_template('showItem.html', user=user, item=item)

    else:
        return render_template('showItem.html', user='', item=item)


def savePicture(file, id):
    '''
    Save uploaded picture for an item into static folder.
    Return the filename of the picture which will be id of item
    with random string for uniqueness plus the extension.
    '''

    extension = file.filename.rsplit('.', 1)[1]
    # Check for valid filename extension for saving a picture,
    # else don't save.
    if extension.lower() in ALLOWED_EXTENSIONS:
        # Generate random variable for unique picture file name.
        randString = ''.join(
            random.choice(string.ascii_lowercase + string.digits) for
            x in xrange(5))

        # Create the filename.
        fileName = str(id) + randString + '.' + extension
        # Save the picture file to the server.
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fileName))
        return fileName

    else:
        flash("Could not save picture. Not a recognised image file.")
        return ''


def removeCategoryPictures(category_id):
    ''' Remove all pictures for items in a category. '''
    items = session.query(Item).filter_by(category_id=category_id)
    for item in items:
        # Delete old picture
        if item.picture:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.picture))


@app.route('/item/new', methods=['GET', 'POST'])
@login_required
def newItem():
    ''' Add a new item to the database. '''
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=request.form['category_id'],
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()

        # If picture was chosen, save to static folder and update item.
        if request.files['picture']:
            newItem.picture = savePicture(request.files['picture'], newItem.id)
            session.commit()
        flash("New item created!")
        return redirect(url_for('catalog'))

    else:
        user = getUserInfo(login_session['user_id'])
        categories = session.query(Category).all()
        return render_template(
            'newItem.html', user=user, categories=categories)


@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def editItem(item_id):
    ''' Edit an existing item in the database. '''
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except:
        flash("That item does not exist!")
        return redirect(url_for('catalog'))

    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = request.form['category_id']

        # If new picture was chosen.
        if request.files['picture']:
            # Delete old picture
            if item.picture:
                os.remove(os.path.join(
                    app.config['UPLOAD_FOLDER'], item.picture))

            # Save new picture to static folder and update item
            item.picture = savePicture(request.files['picture'], item.id)

        session.commit()
        flash("Item modified!")
        return redirect(url_for('catalog'))

    else:
        # Only edit if item belongs to user, otherwise redirect.
        if item.user_id == login_session['user_id']:
            user = getUserInfo(login_session['user_id'])
            categories = session.query(Category).all()
            return render_template(
                'editItem.html', user=user, item=item, categories=categories)

        else:
            flash("You may not edit an item that does not belong to you!")
            return redirect(url_for('catalog'))


@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(item_id):
    ''' Delete item from database. '''
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except:
        flash("That item does not exist!")
        return redirect(url_for('catalog'))

    if request.method == 'POST':
        if item.picture:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.picture))
        session.delete(item)
        session.commit()
        flash("Item deleted!")
        return redirect(url_for('catalog'))

    else:
        # Only delete if item belongs to user, otherwise redirect.
        if item.user_id == login_session['user_id']:
            user = getUserInfo(login_session['user_id'])
            return render_template('deleteItem.html', user=user, item=item)
        else:
            flash("You may not delete an item that does not belong to you!")
            return redirect(url_for('catalog'))


# Error Pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('405.html'), 405


@app.errorhandler(500)
def internal_server_error(e):
    session.rollback()
    return render_template('500.html'), 500


# User Info
def getUserId(email):
    '''
    Get and return user id if email is registered, return none if email
    is not in database.
    '''
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    ''' Return user object. '''
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    ''' Create a new user in database. '''
    try:
        newUser = User(
            name=login_session['username'], email=login_session['email'],
            picture=login_session['picture'])

        session.add(newUser)
        session.commit()
        return user.id
    except:
        session.rollback()
        flash("Could not store new user!")
        return None


if __name__ == '__main__':
    app.secret_key = "Udacity_Project_3_Secret"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
