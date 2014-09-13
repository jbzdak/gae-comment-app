# -*- coding: utf-8 -*-
from google.appengine.api import users

import jinja2
import webapp2

import main


def create_envioronment(debug):
    env = jinja2.Environment(
        loader=jinja2.PackageLoader("comments")
    )
    env.globals['debug'] = debug
    env.globals['current_user'] = users.get_current_user
    env.globals['STATIC_URL'] = "/static"
    return env


def get_enviorment():
    """
    I know that this is not thread safe, but:

    * Their example code works in the same way
    * It doesn't matter if some enviorments will be
      duplicated --- at least it is a pefroemance issue
      it shouldn't break the system.

    :return: Environment
    :rtype: :class:`jinja2.Environment`
    """
    app = webapp2.get_app()
    env = app.registry.get('jinja2.env')
    if env is None:
        app.registry['jinja2.env'] = create_envioronment(main.debug)
        env = app.registry.get('jinja2.env')
    return env