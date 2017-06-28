#! /usr/bin/env python
# -*-coding: utf-8 -*-

__author__ = 'dracarysX'

from collections import deque
from peewee import Expression, ForeignKeyField

from rest_query.operator import Operator, operator_list
from rest_query.query import QueryBuilder
from rest_query.parser import BaseParamsParser, cache_property
from rest_query.models import ModelExtra
from rest_query.serializer import BaseSerializer


class PeeweeModelExtraMixin(ModelExtra):
    """
    peewee model mixin
    """
    all_field = '*'

    def push_join_model(self, field, model):
        if model not in self.join_model:
            self.join_model[model] = (field == model.id)

    def field_by_model(self, model, field_name):
        if field_name == self.all_field:
            return model
        return model._meta.fields[field_name]

    def is_field_exist(self, model, field_name):
        if field_name == self.all_field:
            return True
        return field_name in model._meta.fields

    def foreign_model(self, field):
        return field.rel_model


class PeeweeOperator(Operator):
    """
    operator for peewee orm
    :field: field must be peewee Field instance
    """
    def __init__(self, field, value):
        super(PeeweeOperator, self).__init__(field, value)

    def __getattribute__(self, value, *args, **kwargs):
        if value in operator_list or value == 'iin':
            result = super(PeeweeOperator, self).__getattribute__(value, *args, **kwargs)()

            def _(*args, **kwargs):
                return Expression(result['field'], result['op'], result['value'])

            return _
        return super(PeeweeOperator, self).__getattribute__(value, *args, **kwargs)

    def between(self):
        low, high = self._split_value()
        from peewee import Clause, R
        return self.format('between', value=Clause(low, R('AND'), high))


class PeeweeParamsParser(PeeweeModelExtraMixin, BaseParamsParser):
    
    operator_engine = PeeweeOperator

    def __init__(self, params_args, model=None, **kwargs):
        super(PeeweeParamsParser, self).__init__(params_args, **kwargs)
        self.model = model
        self.foreign_key = ForeignKeyField

    def parse_select(self):
        selects = super(PeeweeParamsParser, self).parse_select()
        self.select_list = list(filter(self.check_field_exist, selects))
        return [self.get_field(select) for select in self.select_list]

    def split_where(self):
        _wheres = []
        for field, values in self.where_args.items():
            try:
                _value = values.split('.')
                operator, value = _value[0], '.'.join(_value[1:])
            except AttributeError:
                operator, value = '=', values
            if self.check_field_exist(field):
                if operator not in self.operator_list:
                    _wheres.append(self.operator_engine(self.get_field(field), values).eq())
                else:
                    _wheres.append(
                        getattr(self.operator_engine(self.get_field(field), value), operator)()
                    )
        return _wheres

    def parse_order(self):
        orders = super(PeeweeParamsParser, self).parse_order()
        _order = []
        for order in orders:
            for k, v in order.items():
                if self.check_field_exist(k):
                    _order.append(getattr(self.get_field(k), v)())
        return _order

    def parse_paginate(self):
        paginate = super(PeeweeParamsParser, self).parse_paginate()
        return (paginate['page'], paginate['limit'])


class PeeweeQueryBuilder(QueryBuilder):
    """
    query builder for peewee orm
    """
    parser_engine = PeeweeParamsParser

    def __init__(self, model, params, **kwargs):
        super(PeeweeQueryBuilder, self).__init__(model, params, **kwargs)

    def build(self):
        query = self.model.select(*self.select)
        if self.where:
            query = query.where(*self.where)
        if self.order:
            query = query.order_by(*self.order)
        for model, condition in self.parser.join_model.items():
            query = query.join(model, on=condition)
        return query.paginate(*self.paginate)


class PeeweeSerializer(BaseSerializer):
    """
    serializer for peewee object instance.
    >>> serializer = PeeweeSerializer(obj=book, select_args=['id', 'name', 'author.id', 'author.name'])
    >>> serializer.data()
    {
        'id': xxx,
        'name': 'xxx',
        'author': {
            'id': xxx,
            'name': 'xxx'
        }
    }
    >>> serializer = PeeweeSerializer(object_list=book_list, select_args=['id', 'name', 'author.id', 'author.name'])
    >>> serializer.data()
    [
        {
            'id': xxx,
            'name': 'xxx',
            'author': {
                'id': xxx,
                'name': 'xxx'
            }
        },
        {
            'id': xxx,
            'name': 'xxx',
            'author': {
                'id': xxx,
                'name': 'xxx'
            }
        }
    ]
    """
    def _obj_update(self, o1, o2):
        """
        o1 update o2, if key in o1 not override
        """
        for key, value in o2.items():
            if key not in o1 or (key in o1 and isinstance(o1[key], int)):
                o1[key] = value
        return o1

    def obj_serializer(self, obj):
        return {k: getattr(obj, k if not isinstance(v, ForeignKeyField) else '%s_id' % k)
                for k, v in obj.__class__._meta.fields.items()}

    def _getattr(self, obj, field):
        value = getattr(obj, field)
        if hasattr(value, 'DoesNotExist'):
            return getattr(obj, '{}_id'.format(field))
        return value

    def serializer(self, obj):
        if not self.select_args:
            return self.obj_serializer(obj)
        data = {}

        def _serializer(_data, select, obj):
            args = select.split('.')
            if len(args) == 1:
                if select == '*':
                    _data = self._obj_update(_data, self.obj_serializer(obj))
                    # _data.update(self.obj_serializer(obj))
                else:
                    if select not in _data:
                        _data[select] = self._getattr(obj, select)
                    else:
                        if not isinstance(_data[select], dict):
                            _data[select] = self._getattr(obj, select)
            else:
                prefix = args[0]
                if prefix not in _data:
                    _data[prefix] = {}
                _serializer(_data[prefix], '.'.join(args[1:]), getattr(obj, prefix))

        for i in self.select_args:
            _serializer(data, i, obj)
        return data

    # def serializer(self, obj):
    #     """
    #     single obj serializer.
    #     """
    #     if self.select_args is None:
    #         return self.obj_serializer(obj)
    #     d = {}

    #     def _get_instance(_obj, _key):
    #         """
    #         >>> _get_instance(book, 'author.school')
    #         author
    #         """
    #         k = _key.split('.')
    #         k.reverse()
    #         instance = _obj
    #         while len(k) > 0:
    #             v = k.pop()
    #             if instance is not None and v in instance._meta.fields:
    #                 instance = getattr(instance, v)
    #             else:
    #                 instance = None
    #         return instance

    #     def _serializer(args):
    #         for arg in args:
    #             if not isinstance(arg, list):
    #                 v = arg.rsplit('.', 1)
    #                 if len(v) == 1:
    #                     if v[0] in obj._meta.fields:
    #                         if isinstance(obj._meta.fields[v[0]], ForeignKeyField):
    #                             d[v[0]] = getattr(obj, '{}_id'.format(v[0]))
    #                         else:
    #                             d[v[0]] = getattr(obj, v[0])
    #                 else:
    #                     if v[1] == '*':
    #                         set_dict(d, v[0], self.obj_serializer(_get_instance(obj, v[0])))
    #                     else:
    #                         _model = _get_instance(obj, v[0])
    #                         if v[1] in _model._meta.fields:
    #                             set_dict(d, arg, getattr(_model, v[1]))
    #             else:
    #                 _serializer(arg)

    #     if len(self.select_args) == 0:
    #         return self.obj_serializer(obj)
    #     _serializer(self.select_args)
    #     return d
