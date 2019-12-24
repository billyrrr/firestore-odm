import setuptools

setuptools.setup(name='firestore_odm',
                 version="0.0.1.dev5",
                 description='Firestore Object Document Mapping. ',
                 author='Bill Rao',
                 author_email='billrao@me.com',
                 url='https://github.com/billyrrr/firestore-odm',
                 download_url='https://github.com/billyrrr/firestore-odm/archive/0.0.1.dev5.tar.gz',
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
                 packages=setuptools.find_packages(),
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
