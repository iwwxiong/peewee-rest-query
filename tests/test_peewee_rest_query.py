#! /usr/bin/env python
# -*-coding: utf-8 -*-
__author__ = 'dracarysX'

import unittest
from peewee import *
from peewee_rest_query import *


# define peewee model
class School(Model):
    id = IntegerField()
    name = CharField()


class Author(Model):
    id = IntegerField()
    name = CharField()
    school = ForeignKeyField(School)


class Book(Model):
    id = IntegerField()
    name = CharField()
    author = ForeignKeyField(Author)


class PeeweeOperatorTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.operator_v1 = PeeweeOperator('name', 'Python')
        cls.operator_v2 = PeeweeOperator('author.school.id', 1)
        cls.operator_v3 = PeeweeOperator('author.id', '10,20')

    def test_eq(self):
        node = self.operator_v1.eq()
        self.assertEqual(node.lhs, Book.name)
        self.assertEqual(node.op, '=')
        self.assertEqual(node.rhs, 'Python')
    
    def test_neq(self):
        node = self.operator_v1.neq()
        self.assertEqual(node.lhs, Book.name)
        self.assertEqual(node.op, '!=')
        self.assertEqual(node.rhs, 'Python')
    
    def test_gt(self):
        node = self.operator_v2.gt()
        self.assertEqual(node.lhs, School.id)
        self.assertEqual(node.op, '>')
        self.assertEqual(node.rhs, 1)
    
    def test_gte(self):
        node = self.operator_v2.gte()
        self.assertEqual(node.lhs, School.id)
        self.assertEqual(node.op, '>=')
        self.assertEqual(node.rhs, 1)
    
    def test_lt(self):
        node = self.operator_v2.lt()
        self.assertEqual(node.lhs, School.id)
        self.assertEqual(node.op, '<')
        self.assertEqual(node.rhs, 1)
    
    def test_lte(self):
        node = self.operator_v2.lte()
        self.assertEqual(node.lhs, School.id)
        self.assertEqual(node.op, '<=')
        self.assertEqual(node.rhs, 1)

    def test_like(self):
        node = self.operator_v1.like()
        self.assertEqual(node.lhs, Book.name)
        self.assertEqual(node.op, 'like')
        self.assertEqual(node.rhs, 'Python')
    
    def test_ilike(self):
        node = self.operator_v1.ilike()
        self.assertEqual(node.lhs, Book.name)
        self.assertEqual(node.op, 'ilike')
        self.assertEqual(node.rhs, 'Python')

    def test_in(self):
        node = self.operator_v3.iin()
        self.assertEqual(node.lhs, Author.id)
        self.assertEqual(node.op, 'in')
        self.assertListEqual(node.rhs, [10, 20])

    # def test_between(self):
    #     node = self.operator_v3.between()
    #     self.assertEqual(node.lhs, Author.id)
    #     self.assertIsInstance(node.rhs, Clause)


class PeeweeParamsParserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = {
            'select': 'id,name,author{id,name,abc,school{id,name}}',
            'id': 'gt.10', 
            'age': 'lte.25',
            'name.in': 'in.python, javascript',
            'order': 'id.desc',
            'page': 2,
            'limit': 5
        }
        cls.parser = PeeweeParamsParser(params_args=args, model=Book)
    
    def test_parse_select(self):
        self.assertEqual(len(self.parser.parse_select()), 6)
        self.assertIn(Book.id, self.parser.parse_select())
        self.assertIn(Book.name, self.parser.parse_select())
        self.assertIn(Author.id, self.parser.parse_select())
        self.assertIn(Author.name, self.parser.parse_select())
        self.assertIn(School.id, self.parser.parse_select())
        self.assertIn(School.name, self.parser.parse_select())

    def test_parse_where(self):
        pass
        # self.assertEqual(len(self.parser.parse_where()), 2)
        # self.assertIn(Expression(Book.id, '>', 10), self.parser.parse_where())
        # self.assertIn(Expression(Book.name, '<<', ['python, javascript']), self.parser.parse_where())

    def test_parse_order(self):
        self.assertEqual(self.parser.parse_order()[0]._ordering, 'DESC')

    def test_parse_paginate(self):
        self.assertTupleEqual(self.parser.parse_paginate(), (2, 5))


class PeeweeQueryBuilderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = {
            'select': 'id,name,author{id,name,abc,school{id,name}}',
            'id': 'in.10,15', 
            'age': 'lte.25',
            'name': 'ilike.python',
            'order': 'id.desc',
            'page': 2,
            'limit': 5
        }
        cls.builder = PeeweeQueryBuilder(Book, args)

    def test_build(self):
        query = self.builder.build()
        q = Book.select(
            Book.id, Book.name, Author.id, Author.name, School.id, School.name
        ).where(
            Book.id << [10, 15], Book.name ** 'python'
        ).order_by(
            Book.id.desc()
        ).join(
            Author, on=(Book.author == Author.id)
        ).join(
            School, on=(Author.school == School.id)
        ).paginate(2, 5)
        print(query.sql()[0])
        self.assertTrue(query.sql()[0].endswith(
            '''WHERE (("t1"."name" LIKE ?) AND ("t1"."id" IN (?, ?))) ORDER BY "t1"."id" DESC LIMIT 5 OFFSET 5'''
        ))
