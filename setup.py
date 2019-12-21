import setuptools
from packagename.version import Version


setuptools.setup(name='firestore-odm',
                 version=Version('1.0.0').number,
                 description='Firestore Object Document Mapping. ',
                 long_description=open('README.md').read().strip(),
                 author='Bill Rao',
                 author_email='billrao@me.com',
                 url='http://path-to-my-packagename',
                 py_modules=['firestore_odm'],
                 install_requires=[
                     'google-auth==1.5.1',
                     'google-cloud-datastore>=1.4.0',
                     'google-api-python-client',
                     'firebase-admin',
                     # TODO: add version constraint
                     'marshmallow',
                     "inflection",
                     "apispec>=2.0.2",
                     "dictdiffer",
                     "celery"
                 ],
                 license='MIT License',
                 zip_safe=False,
                 keywords=["firebase", "firestore", "ORM",
                           "backend", "nosql"],
                 classifiers=[
                     'Development Status :: 3 - Alpha',
                     'Intended Audience :: Developers',
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                 ])
