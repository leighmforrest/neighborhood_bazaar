# Neighborhood Bazaar
by Leigh Michael Forrest

Website: [https://neighborhood-bazaar-19125.herokuapp.com](https://neighborhood-bazaar-19125.herokuapp.com)

JSON Endpoints:

 [https://neighborhood-bazaar-19125.herokuapp.com/category/json](https://neighborhood-bazaar-19125.herokuapp.com/category/json)

[https://neighborhood-bazaar-19125.herokuapp.com/item/json](https://neighborhood-bazaar-19125.herokuapp.com/item/json)

---

## Installation on Local Machine.
To start, make sure you are in a virtual environment.

Clone the following git repository: `https://github.com/leighmforrest/neighborhood_bazaar.git`

After cloning, run the following command in the command line: `pip install -r requirements.txt` Please run the one in the git repo, not the one generated from a Vagrant virtual box.

The code needs environment variables to run properly. Create a file called **.env** the following environment variables are required:

**FACEBOOK_ID=[App ID here]**

**FACEBOOK_SECRET=[Secret here]**

**SECRET_KEY=[Any string you like]**

To initialize the database, run the following code in the command line:
`python init.py` This script will generate all of the tables; however, there is no data.

To run the app, run this command: `gunicorn application:app` the application should be running at [127.0.0.1:8000](127.0.0.1:8000) It is strongly suggested to use gunicorn, and not run `python application.py`, as gunicorn is needed to run the app on Heroku.

## Installation on Heroku

Clone the following git repository: https://github.com/leighmforrest/neighborhood_bazaar.git

Visit [Heroku](http://www.heroku.com). If you have not signed up and downloaded the Command Line Interface, do so there.

Once signed up and CLI running, login to Heroku in the CLI: `heroku login` and enter credentials when prompted.

Create an app with this command: `heroku create [appname]`

Push the cloned repository to the app: `git push heroku master`

You will need to add environment variables in Heroku. Run the following commands individually (your values in brackets):

`heroku config:set FACEBOOK_ID=[App ID here]`

`heroku config:set FACEBOOK_SECRET=[Secret here]`

`heroku config:set SECRET_KEY=[Any string you like]`

Heroku uses Postgres to store data. To initialize the Postgres database for your app, run this command: ` heroku addons:create heroku-postgresql:hobby-basic` There will be no need to run any other configuration. Heroku adds an environment variable **DATABASE_URL**, and the source code is already set up to use this environment variable.

Before your app is ready to go, you will need to initialize the database tables. In the command line, run this command: `heroku run bash` When the prompt displays, run this command: `python init.py` Your app should now be ready for operation!
