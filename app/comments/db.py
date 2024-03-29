# -*- coding: utf-8 -*-

from google.appengine.ext import ndb


class Site(ndb.Model):

    siteurl = ndb.StringProperty()
    sitename = ndb.TextProperty()
    owner = ndb.UserProperty(auto_current_user_add=True)
    admins = ndb.UserProperty(repeated=True)


class Commenter(ndb.Model):

    site = ndb.KeyProperty(kind=Site)
    username = ndb.StringProperty()
    e_mail = ndb.StringProperty()
    password = ndb.TextProperty()
    salt = ndb.TextProperty()


class Comment(ndb.Model):
    """Models an individual Guestbook entry with content and date."""

    COMMENT_STATE = ("DECLINED", "UNDECIDED", "APPROVED")

    content = ndb.TextProperty()
    user_e_mail = ndb.StringProperty()
    username = ndb.StringProperty()
    url = ndb.StringProperty()

    full_url = ndb.TextProperty()

    state = ndb.StringProperty(choices=COMMENT_STATE, default=COMMENT_STATE[1])

    site = ndb.KeyProperty(kind=Site)

    date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def query_book(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.date)
