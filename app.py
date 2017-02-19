import random
import string
import httplib2
import json
import requests
from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify, flash, Response, make_response
from flask import session as login_session
from sqlalchemy import desc
from database_setup import Category, CategoryItem, User, DBSession
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from functools import wraps

# App Configuration

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']
APPLICATION_NAME = "Item Catalog App"
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
session = DBSession()

# Helper Methods


def login_required(f):
    # Verifys if the user is logged in or not
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You need to be logged in to add a new item.")
            return redirect(url_for('getMainPage'))
    return decorated_function


def titleExists(title):
    # Verifys if an item exists with the same unique title in db
    results = session.query(CategoryItem).filter_by(title=title).all()
    return len(results) > 0


def get_user_id_by_name(name):
    try:
        user = session.query(User).filter_by(name=name).one()
        return user.id
    except:
        return None


def create_user(login_session):
    username = login_session['username']
    new_user = User(name=username)
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(name=username).one()
    return user.id

# Routes


@app.route('/')
def toMain():
    # Main Page
    return redirect(url_for('getMainPage'))


@app.route('/catalog/JSON')
def getCatalog():
    # Returns JSON version of the catalog
    output_json = []
    categories = session.query(Category).all()
    for category in categories:
        items = session.query(CategoryItem).filter_by(category_id=category.id)
        category_output = {}
        category_output["id"] = category.id
        category_output["name"] = category.name
        category_output["items"] = [i.serialize for i in items]
        output_json.append(category_output)
    return jsonify(Categories=output_json)


@app.route('/catalog/items/<item_title>/JSON')
def getItem(item_title):
    # Returns JSON data of an arbitrary item
    item = session.query(CategoryItem).filter_by(title=item_title).one()
    return jsonify(Team=item.serialize)


@app.route('/catalog', methods=['GET', 'POST'])
def getMainPage():
    # main page logics, includes auth, session management
    try:
        user = login_session['username']
    except KeyError:
        user = None
    if request.method == 'GET':
        STATE = ''.join(random.choice(string.ascii_uppercase +
                                      string.digits) for x in xrange(32))
        login_session['state'] = STATE
        categories = session.query(Category).all()
        latest_items = session.query(CategoryItem).order_by(
            desc(CategoryItem.date)).all()
        category_names = {}
        for category in categories:
            category_names[category.id] = category.name
        if len(latest_items) == 0:
            flash("No items found")
        return render_template(
            'category.html', categories=categories, items=latest_items,
            category_names=category_names, user=user, STATE=STATE
        )
    else:
        print ("Starting authentication")
        if request.args.get('state') != login_session['state']:
            response = make_response(json.dumps(
                'Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        # Get authorization code
        code = request.data

        try:
            oauth_flow = flow_from_clientsecrets(
                'client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = make_response(
                json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify if the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
               % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # Check errors in the access token info
        if result.get('error') is not None:
            response = make_response(
                       json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(json.dumps(
                "Token's user ID doesn't match given user ID."), 401)
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
            response = make_response(json.dumps(
                'Current user is already connected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Store the access token in the session
        login_session['access_token'] = credentials.access_token
        login_session['gplus_id'] = gplus_id

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)
        data = answer.json()
        login_session['username'] = data['name']

        user_id = get_user_id_by_name(data['name'])
        if not user_id:
            user_id = create_user(login_session)
        login_session['user_id'] = user_id

        flash("you are now logged in as %s" % login_session['username'])
        return redirect(url_for('getMainPage'))


@app.route('/gdisconnect')
def gdisconnect():
    # Disconnecting from Google Auth """
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
        login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('getMainPage'))
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/categories/<category_name>/')
def getCategoryItems(category_name):
    # Displaying items for a given division
    categories = session.query(Category).all()
    selected_category = session.query(
        Category).filter_by(name=category_name).one()
    items = session.query(CategoryItem).filter_by(
        category_id=selected_category.id).all()
    category_names = {}
    for category in categories:
        category_names[category.id] = category.name
    if len(items) == 0:
        flash("No teams found in this division")
    try:
        user = login_session['username']
    except KeyError:
        user = None
    return render_template(
        'category_items.html', selected_category=selected_category,  user=user,
        items=items, categories=categories, category_names=category_names
    )


@app.route('/catalog/items/<item_title>/')
def getItemDetails(item_title):
    # Displaying a specific team object given its title
    item = session.query(CategoryItem).filter_by(title=item_title).one()
    category = session.query(Category).filter_by(id=item.category_id).one()
    return render_template(
        'item.html', item=item, category=category
    )


@app.route('/catalog/items/new', methods=['GET', 'POST'])
@login_required
def newItem():
    # Creating a new item """
    categories = session.query(Category).all()
    try:
        user = login_session['username']
    except KeyError:
        user = None
    if request.method == 'POST':
        title = request.form['title']
        if titleExists(title):
            flash("Please enter a different team. Team " +
                  title + " already exists.")
            return redirect(url_for('newItem'))
        user_id = get_user_id_by_name(login_session['username'])
        newItem = CategoryItem(title,
                               request.form['description'],
                               request.form['category_id'],
                               user_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('getMainPage'))
    else:
        return render_template(
            'create.html', categories=categories, user=user
        )


@app.route('/catalog/items/<item_title>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(item_title):
    # Deleting an item given its title
    item = session.query(CategoryItem).filter_by(title=item_title).one()
    if item.user_id != login_session['user_id']:
        flash("You are not authorized to delete this team.")
        return redirect(url_for('getMainPage'))
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('getMainPage'))
    else:
        user = login_session['username']
        return render_template(
            'delete.html', item_title=item_title, user=user
        )


@app.route('/catalog/items/<item_title>/edit', methods=['GET', 'POST'])
@login_required
def editItem(item_title):
    # Updating an existing item """
    editedItem = session.query(CategoryItem).filter_by(title=item_title).one()
    if editedItem.user_id != login_session['user_id']:
        flash("You are not authorized to edit this team.")
        return redirect(url_for('getMainPage'))
    category = session.query(Category).filter_by(
        id=editedItem.category_id).one()
    categories = session.query(Category).all()
    if request.method == 'POST':
        if request.form['title']:
            title = request.form['title']
            if item_title != title and titleExists(title):
                flash("Please enter a different team. Team " +
                      title + " already exists.")
                return redirect(url_for('editItem', item_title=item_title))
            editedItem.title = title
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category_id']:
            editedItem.category_id = request.form['category_id']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('getMainPage'))
    else:
        user = login_session['username']
        return render_template(
            'edit.html', item=editedItem, category=category,
            categories=categories, user=user
        )

if __name__ == '__main__':
    app.secret_key = 'secret'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
