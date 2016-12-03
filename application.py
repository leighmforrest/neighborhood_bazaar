import os
from os.path import abspath, dirname, join
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

from flask import (Flask, redirect, render_template, url_for,
                   abort, flash, jsonify)
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         current_user, login_required)
from wtforms import fields
from wtforms.validators import DataRequired
from oauth import OAuthSignIn


# Load the environment variables
load_dotenv(find_dotenv())

_cwd = dirname(abspath(__file__))

SECRET_KEY = os.environ['SECRET_KEY']
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(_cwd, 'flask-tracking.db')
WTF_CSRF_SECRET_KEY = 'this-should-be-more-random'


app = Flask(__name__)
app.config.from_object(__name__)

app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': os.environ['FACEBOOK_ID'],
        'secret': os.environ['FACEBOOK_SECRET']
    },
}

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref(
        'category_users', lazy='dynamic'))

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return "{}".format(self.name)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref=db.backref(
        'items', lazy='dynamic'))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref(
        'item_users', lazy='dynamic'))

    def __str__(self):
        return "<Item: {}".format(self.name)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'user': self.user.social_id,
            'nickname': self.user.nickname
        }


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


# Forms
def get_categories():
    """Helper function to populate select fields with current categories."""
    categories = Category.query.all()
    return [(category.id, category.name) for category in categories]


class DeleteCategoryForm(FlaskForm):
    delete = fields.SubmitField('Delete')


class DeleteItemForm(FlaskForm):
    delete = fields.SubmitField('Delete')


class ItemForm(FlaskForm):
    name = fields.StringField('name', validators=[DataRequired()])
    description = fields.TextAreaField('description')
    category = fields.SelectField(u'Category', coerce=int)


class CategoryForm(FlaskForm):
    name = fields.StringField('name', validators=[DataRequired()])
    description = fields.TextAreaField('description')

# Main Routes
def is_owner(entity, current_user):
    """Test if object's user is the logged-in user."""
    return entity.user == current_user


@app.route('/')
def index():
    categories = Category.query.all()
    items = Item.query.all()
    return render_template("index.html", categories=categories, items=items)


@app.route('/category/new', methods=('GET', 'POST'))
@login_required
def add_category():
    user = current_user
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(form.name.data, form.description.data)
        category.user = current_user
        db.session.add(category)
        db.session.commit()
        flash("Category {} added!".format(category.name))
        return redirect(url_for("index"))
    return render_template("add_category.html", form=form)


@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get(category_id)
    if not is_owner(category, current_user):
        abort(404)

    user = current_user
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        category.user = user
        db.session.commit()
        flash("Category {} updated!".format(category.name))
        return redirect('/')
    return render_template('edit_category.html', form=form, category=category)


@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if not is_owner(category, current_user):
        abort(404)
    form = DeleteCategoryForm()
    if form.validate_on_submit():
        message = "Category {} deleted!".format(category.name)
        db.session.delete(category)
        db.session.commit()
        flash(message)
        return redirect('/')
    else:
        return render_template('delete_category.html', category=category, form=form)

@app.route('/category/<int:category_id>')
def show_category(category_id):
    category = Category.query.get(category_id)
    items = Item.query.filter_by(category=category)
    return render_template('category.html', category=category, items=items)


@app.route('/item/new', methods=('GET', 'POST'))
@login_required
def add_item():
    form = ItemForm()
    form.category.choices = get_categories()
    if form.validate_on_submit():
        category = Category.query.get(form.category.data)
        item = Item(
            category=category,
            name=form.name.data,
            description=form.description.data,
            user=current_user)
        item.pub_date = datetime.now()
        db.session.add(item)
        db.session.commit()
        flash("Item \"{}\" added!".format(item.name))
        return redirect(url_for("index"))
    return render_template("add_item.html", form=form)


@app.route('/item/<int:item_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if not is_owner(item, current_user):
        abort(404)
    form = ItemForm(obj=item)
    form.category.choices = get_categories()
    if form.validate_on_submit():
        # fields need to be done separately because of the category field.
        item.category = Category.query.get(form.category.data)
        item.name = form.name.data
        item.description = form.description.data
        db.session.commit()
        flash("Item \"{}\" updated!".format(item.name))
        return redirect(url_for("index"))
    return render_template("edit_item.html", form=form, item=item)

@app.route('/item/<int:item_id>')
def show_item(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item.html', item=item)


@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if not is_owner(item, current_user):
        abort(404)
    form = DeleteCategoryForm()
    if form.validate_on_submit():
        message = "Item \"{}\" deleted!".format(item.name)
        db.session.delete(item)
        db.session.commit()
        flash(message)
        return redirect('/')
    else:
        return render_template('delete_item.html', item=item, form=form)


# OAUTH Routes
@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    message = "User logged off successfully!"
    logout_user()
    flash(message)
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    flash("Facebook user \"{}\" logged in!".format(user.nickname))
    return redirect(url_for('index'))

# JSON Endpoints
@app.route('/item/json')
def items_json():
    items = Item.query.all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/category/json')
def categories_json():
    categories = Category.query.all()
    return jsonify(Categories=[i.serialize for i in categories])

if __name__ == '__main__':

    app.debug = True
    app.run(host='0.0.0.0', port=5000)
