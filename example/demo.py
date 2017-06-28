#! /usr/bin/env python
# -*-coding: utf-8 -*-
__author__ = 'dracarysX'

import os
import sys
from flask import Flask, request, jsonify
from peewee import *
from flask_peewee.db import Database
from flask.views import MethodView
from peewee_rest_query import PeeweeQueryBuilder, PeeweeSerializer

# configure our database
DATABASE = {
    'name': 'example.db',
    'engine': 'peewee.SqliteDatabase',
}
DEBUG = True
SECRET_KEY = 'dracarysX'

app = Flask(__name__)
app.config.from_object(__name__)

# instantiate the db wrapper
db = Database(app)


class School(db.Model):
    id = PrimaryKeyField()
    name = CharField(max_length=100)


class Publisher(db.Model):
    id = PrimaryKeyField()
    name = CharField(max_length=100)


class Author(db.Model):
    """
    Author model
    """
    id = PrimaryKeyField()
    name = CharField(max_length=50)
    age = IntegerField(default=0)
    school = ForeignKeyField(School)

    class Meta:
        db_table = 'Author'

    def __repr__(self):
        return u'<Author {}>'.format(self.name)


class Book(db.Model):
    """
    Book model
    """
    id = PrimaryKeyField()
    name = CharField(max_length=255)
    author = ForeignKeyField(Author)
    publisher = ForeignKeyField(Publisher)

    class Meta:
        db_table = 'Book'

    def __repr__(self):
        return u'<Book {}>'.format(self.name)


@app.route('/')
def home():
    return jsonify({
        'authors': '/authors',
        'books': '/books'
    })


# class AuthorView(MethodView):

#     model = Author

#     def get(self):
#         builder = PeeweeQueryBuilder(model=self.model, params=request.args)
#         query = builder.build()
#         serializer = PeeweeSerializer(object_list=query, select_args=builder.parser.select_list)
#         return jsonify(serializer.data())


# class BookView(MethodView):

#     model = Book

#     def get(self):
#         builder = PeeweeQueryBuilder(model=self.model, params=request.args)
#         query = builder.build()
#         serializer = PeeweeSerializer(object_list=query, select_args=builder.parser.select_list)
#         return jsonify(serializer.data())

# wo can also do this

class BaseView(MethodView):
    
    model = None
    context_object_name = 'object_list'

    def _detail(self, id):
        args = request.args.copy()
        args.update({
            'id': id
        })
        builder = PeeweeQueryBuilder(model=self.model, params=args)
        try:
            query = builder.build().get()
        except self.model.DoesNotExist:
            return jsonify({'code': 404, 'message': 'NotFound'})
        serializer = PeeweeSerializer(
            obj=query, 
            select_args=builder.parser.select_list
        )
        return jsonify(serializer.data())

    def _list(self):
        builder = PeeweeQueryBuilder(model=self.model, params=request.args)
        query = builder.build()
        serializer = PeeweeSerializer(
            object_list=query, 
            select_args=builder.parser.select_list
        )
        data = {
            self.context_object_name: serializer.data(),
            'count': query.count(),
        }
        return jsonify(data)

    def get(self, id):
        if id is not None:
            return self._detail(id)
        return self._list()


class PublisherView(BaseView):
    model = Publisher
    context_object_name = 'publisher_list'


class SchoolView(BaseView):
    model = School
    context_object_name = 'school_list'


class AuthorView(BaseView):
    model = Author
    context_object_name = 'author_list'


class BookView(BaseView):
    model = Book
    context_object_name = 'book_list'


def register_api(view, endpoint, url, pk='id', pk_type='int'):
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET'])
    app.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
                     methods=['GET'])


register_api(SchoolView, 'school_api', '/schools/')
register_api(PublisherView, 'publisher_api', '/publishers/')
register_api(AuthorView, 'author_api', '/authors/')
register_api(BookView, 'book_api', '/books/')


if __name__ == '__main__':
    if sys.argv[1] == 'runserver':
        app.run()
    elif sys.argv[1] == 'initdata':
        if os.path.exists('example.db'):
            os.remove('example.db')
        # init database and create data
        School.create_table(fail_silently=True)
        Publisher.create_table(fail_silently=True)
        Author.create_table(fail_silently=True)
        Book.create_table(fail_silently=True)

        s1 = School.create(name='BJ University')
        s2 = School.create(name='HB University')
        p1 = Publisher.create(name='XXXX')
        p2 = Publisher.create(name='YYYY')
        a1 = Author.create(name='wwxiong', age=20, school=s2)
        a2 = Author.create(name='dracarysx', age=100, school=s1)
        b1 = Book.create(name='Python', author=a1, publisher=p2)
        b2 = Book.create(name='Javascript', author=a2, publisher=p1)
        print('Init data completed')
