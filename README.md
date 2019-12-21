firestore-odm
==========================

Firestore-odm maps Firestore document to objects. 

This framework is at development stage. API is not guaranteed and may change often. 

## Installation
In your project's requirements.txt, 

```

# Append to requirements, unless repeating existing requirements

google-cloud-firestore
firestore-odm  # Not released to pypi yet 

```

Configure virtual environment 
```
pip install virtualenv
virtualenv env
source env/bin/activate
```

In your project directory, 

```
pip install -r requirements.txt
```

See more in [Quickstart](https://flask-boiler.readthedocs.io/en/latest/quickstart_link.html). 

## Usage

### Context Management
In `__init__` of your project source root:
```python
import os

from firestore_odm import context
from firestore_odm import config

Config = config.Config

testing_config = Config(app_name="your_app_name",
                        debug=True,
                        testing=True,
                        certificate_path=os.path.curdir + "/../your_project/config_jsons/your_certificate.json")

CTX = context.Context
CTX.read(testing_config)
```

Note that initializing `Config` with `certificate_path` is unstable and
may be changed later.

In your project code,

```python
from firestore_odm import context

CTX = context.Context

# Retrieves firestore database instance 
CTX.db

# Retrieves firebase app instance 
CTX.firebase_app

```


### Add data

```python
user = User.new(doc_id="alovelace", first = 'Ada', last = 'Lovelace')
user.born = "1815"
user.save()
```

(*Extra steps required to declare model. See quickstart for details.)

### Read data

```python
for user in User.all():
    print(user.to_dict())
```

### Save data

```python

def CityBase(DomainModel):
    _collection_name = "cities"
    
City = ClsFactory.create_customized(
        name="City",
        fieldnames=["name", "state", "country", "capital", "population", "regions"], 
        auto_initialized=False,
        importable=False,
        exportable=True,
        additional_base=(CityBase,)
    )
    
City.new(
        doc_id='SF',
        name='San Francisco',
        state='CA', 
        country='USA', 
        capital=False, 
        populations=860000,
        regions=['west_coast', 'norcal']).save()

# ...
```

(*fieldname kwarg in ClsFactory to be implemented soon)

### Get data

```python
sf = City.get(doc_id='SF')
if sf is not None:  # To be implemented soon  
    print(u'Document data: {}'.format(doc.to_dict()))
else:
    print("No such document")

```

### Relationship

Flask-boiler adds an option to retrieve a relation with 
minimal steps. Take an example given from SQLAlchemy, 

```python
category_id = utils.random_id()
py = Category.create(doc_id=category_id)
py.name = "Python"

post_id = utils.random_id()
p = Post.create(doc_id=post_id)
p.title = "snakes"
p.body = "Ssssssss"

# py.posts.append(p)
p.category = py

py.save()

obj = Post.get(doc_id=post_id)

assert str(p.category) == "<Category 'Python'>"

assert p._export_as_view_dict() == {'body': 'Ssssssss',
                                    'id': post_id,
                                    'category': {
                                        'id': category_id,
                                        'name': 'Python'},
                                    'title': 'snakes',
                                    'pubDate': None
                                    }
                                    
```

See ```examples/relationship_example.py```

### Embedded

You can embed a serializable object in a ViewModel or ReferencedObject, 
so that the embedded object is retrieved with the master object 
(no separate calls). Thus offer an advantage over performance when 
1. nested document is meant to be retrieved with the master document
2. nested document is not referenced by any other document 
3. nested documents do not need to be queried 


```python
class TargetSchema(schema.Schema):
    earliest = fields.Raw()
    latest = fields.Raw()

class Target(serializable.Serializable):
    _schema_cls = TargetSchema

t = Target()
t.earliest = 10
t.latest = 20

class PlanSchema(schema.Schema):
    target = fields.Embedded()
    name = fields.Str()

class Plan(serializable.Serializable):
    _schema_cls = PlanSchema

k = Plan.from_dict({
    "target": t.to_dict(),
    "name": "my plan"
})

assert k.to_dict() == {
    "name": "my plan",
    "target": {
        "earliest": 10,
        "latest": 20,
        "obj_type": "Target",
        "doc_id": ""
    },
    "obj_type": "Plan",
    "doc_id": ""
}

```

## Contributing
Pull requests are welcome. 

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)