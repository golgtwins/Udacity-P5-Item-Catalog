# Udacity Full Stack Nanodegree Project 5: Item Catalog
NHL Teams (Item Catalog) application built with Flask.

A web application that provides a list of items within a category. Users can sign in using google sign-in and add/edit/delete Items.

This application is built using Python and the [Flask](http://flask.pocoo.org/) lightweight web framework. An sqlite database is used for storing the catalog data.

List of libraries/frameworks/APIs found in this project:
* [Flask](http://flask.pocoo.org/) A lightweight web framework for Python.
* [SQLAlchemy](www.sqlalchemy.org) - Python SQL Toolkit and Object Relational Mapper.
* [Bootstrap](http://getbootstrap.com/) - CSS Framework for quick and easy basic grid layout and css elements.
* [Google Sign-In for Websites](https://developers.google.com/identity/sign-in/web/sign-in) - Get users into your apps quickly and securely, using a registration system they already use and trust.

# How to run the application:
- Run `pip install -r requirements.txt` to install the dependency libraries (Flask, sqlalchemy, requests and oauth2client, included in the requirements.txt file).
- Run `python db_seed.py` to populate the database.
- Run `python app.py` to fire up the server at port 8000.
- Go to url localhost:8000 at the browser to check the web app.

# Application breakdowns
- Routing and Templating implemented with Flask.
- Google+ Login used to authenticate users for creating, editing and deleting teams.
- SQLAlchemy used as the ORM to communicate with the database.
- RESTful API endpoints that return json files.
- Front-end UI built with twitter Bootstrap.


