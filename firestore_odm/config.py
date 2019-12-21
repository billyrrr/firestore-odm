"""
Author: Zixuan Rao
Reference:
    http://flask.pocoo.org/docs/1.0/config/
    https://medium.freecodecamp.org/structuring-a-flask-restplus-web-service-for-production-builds-c2ec676de563
"""

import os

caller_module_path = os.path.curdir
config_jsons_path = os.path.join(caller_module_path, "config_jsons")


class Config:
    """
    TESTING: (authenticate decorator will return uid as the value of header["Authentication"])
        Enable testing mode. Exceptions are propagated rather than handled by the the app’s error handlers.
        Extensions may also change their behavior to facilitate easier testing.
        You should enable this in your own tests.
    DEBUG:
        Whether debug mode is enabled.
        When using flask run to start the development server, an interactive debugger will be shown for unhandled
        exceptions, and the server will be reloaded when code changes. The debug attribute maps to this config key.
        This is enabled when ENV is 'development' and is overridden by the FLASK_DEBUG environment variable.
        It may not behave as expected if set in code.

    Note that this Config currently does not affect (Flask) main.app CONFIG.
    TODO: extend from Flask Config and apply to main.app

    """
    DEBUG: bool = None
    TESTING: bool = None
    FIREBASE_CERTIFICATE_JSON_PATH: str = None
    APP_NAME: str = None

    def __new__(cls, certificate_filename=None, certificate_path=None,
                testing=False, debug=False,
                app_name=None, *args, **kwargs):
        if certificate_path is not None:
            cls.FIREBASE_CERTIFICATE_JSON_PATH = certificate_path
        else:
            cls.FIREBASE_CERTIFICATE_JSON_PATH = os.path.join(
                config_jsons_path, certificate_filename)
        cls.TESTING = testing
        cls.DEBUG = debug
        cls.APP_NAME = app_name
        return cls
