# peewee-rest-query

A rest query request args parser for peewee orm. like no-sql select style.(/?select=id,name,author{*}&id=gte.20&order=id.desc).

## Installing

    > pip install peewee-rest-query

## Test

    > python setup.py test

## Usage

```python
> from peewee_rest_query import PeeweeQueryBuilder, PeeweeSerializer
> class School(Model):
     id = PrimaryKeyField()
     name = CharField(max_length=100)

> class Author(Model):
     id = PrimaryKeyField()
     name = CharField(max_length=50)
     age = IntegerField(default=0)
     school = ForeignKeyField(School)

> class Book(Model):
     id = PrimaryKeyField()
     name = CharField(max_length=255)
     author = ForeignKeyField(Author)

> args = {
        'select': 'id,name,author{id,name,school{*}}',
        'id': 'gte.20',
        'author.id': 'in.10,20,30,40,50',
        'order': 'id.desc',
        'page': 1,
        'limit': 5
    }
> builder = PeeweeQueryBuilder(Book, args)
> builder.select
[<class '__main__.School'>, <peewee.PrimaryKeyField object>, <peewee.CharField object>, <peewee.PrimaryKeyField object>, <peewee.CharField object>]
> build.where
[<peewee.Expression object>, <peewee.Expression object>]
> builder.order
[<peewee.PrimaryKeyField object>]
> builder.paginate
(1, 5)
> builder.build()
<class '__main__.Book'> SELECT "t3"."id", "t3"."name", "t2"."id", "t2"."name", "t1"."id", "t1"."name" FROM "book" AS t1 INNER JOIN "author" AS t2 ON ("t1"."author_id" = "t2"."id") INNER JOIN "school" AS t3 ON ("t2"."school_id" = "t3"."id") WHERE (("t1"."id" >= ?) AND ("t2"."id" IN (?, ?, ?, ?, ?))) ORDER BY "t1"."id" DESC LIMIT 5 OFFSET 0 [20, 10, 20, 30, 40, 50]
```

## License

MIT

## Contacts

Email: huiquanxiong@gmail.com
