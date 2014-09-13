# -*- coding: utf-8 -*-

from hashlib import pbkdf2_hmac

from Crypto.Random import get_random_bytes
from google.appengine.ext import ndb

from comments.db import Comment, Site, Commenter

from google.appengine.api import users


class APIException(Exception):

    def __init__(self, error_code, message):
        self.error_code = error_code
        super(APIException, self).__init__(message)


class NoSuchSiteException(APIException):
    pass


class PostCommentException(APIException):
    pass


class FetchCommentException(APIException):
    pass


class CommenterError(APIException):
    pass


class NoSuchCommenter(CommenterError):
    pass


class CommenterService(object):

    @staticmethod
    def get_commenter(username, site):
        commenters = Commenter.query(Commenter.username == username and Commenter.site == site.key).fetch()
        if len(commenters) == 0:
            raise NoSuchCommenter(400, "Unknown commenter username")
        return commenters[0]

    @classmethod
    def _hash_password(cls, password, salt):
        return pbkdf2_hmac('sha512', password, salt, int(1E5))

    @classmethod
    def _save_commenter(cls, username, password, site):
        if password is None or len(password) == 0:
            return Commenter(
                site=site.key,
                username=username,
            )
        c = Commenter(
            site=site.key,
            username=username,
            salt = get_random_bytes(16)
        )
        c.password = cls._hash_password(password, c.salt)
        c.put()
        return c

    @ndb.transactional
    @classmethod
    def get_or_create_commenter(cls, username, password, site):
        try:
            commenter = cls.get_commenter(username, site)
        except NoSuchCommenter as e:
            return cls._save_commenter(username, password, site)

        expected_hash = cls._hash_password(password, commenter.salt)
        if expected_hash != commenter.password:
            raise CommenterError(403, "Invalid password, and this username is registered")
        return commenter


class SiteService(object):

    @staticmethod
    def site_by_domain(domain, exception_type=NoSuchSiteException):
        sites = Site.query(Site.siteurl == domain).fetch()
        if len(sites) == 0:
            raise exception_type(400, "No such site")
        return sites[0]  # Since we cant guarantee uniqueness, it is better to
                         # silently ignore duplicates than to raise error here

    @staticmethod
    def sites_by_user(user):
        return Site.query(Site.owner == user or Site.admins == user).fetch()


class CommentService(object):

    @staticmethod
    def create_comment_serializer(serialize_key = False):
        def comment_serializer(obj):
            if not isinstance(obj, Comment):
                raise TypeError()
            data = {
                "content": obj.content,
                "username": obj.username,
                "state": obj.state,
                "site": obj.site.get().siteurl,
                "date": obj.date.isoformat()
            }
            if serialize_key:
                data['key'] = obj.key
            return data

    @classmethod
    def validate_can_update_comment(cls, comment):
        site = comment.site.get()
        if users.is_current_user_admin():
            return
        if not site in SiteService.sites_by_user(users.get_current_user()):
            raise CommenterError("401", "Not authorized")

    @classmethod
    def update_comment_contents(cls, comment, new_contents):
        cls.validate_can_update_comment(comment)
        comment.content = new_contents
        comment.put()


    @classmethod
    def update_comment_state(cls, comment, new_state):
        cls.validate_can_update_comment(comment)
        comment.state = new_state
        comment.put()

    @staticmethod
    def filter_posts(url=None, site=None, state=None, user=None):

        query = Comment.query()

        if site:
            if not isinstance(site, Site):
                site = SiteService.site_by_domain(site, FetchCommentException)
                query = query.filter(Comment.site == site.key)

        if state:
            query = query.filter(Comment.state == state)

        if user:
            query = query.filter(Comment.site.IN(SiteService.sites_by_user(user)))

        if url:
            query = query.filter(Comment.url == url)

        return query.fetch()

    @staticmethod
    def posts_for_url(url, domain):

        site = SiteService.site_by_domain(domain, FetchCommentException)

        return Comment.query(Comment.site == site.key and Comment.url == url).order(Comment.date).fetch()

    @staticmethod
    def post_comment(user, comment, url, domain, password):

        site = SiteService.site_by_domain(domain, PostCommentException)
        CommenterService.get_or_create_commenter(user, password, site)
        if comment is None or len(comment) < 15:
            raise PostCommentException(400, "Comment must be longer than 15 letters")
        if user is None or len(user) == 0:
            raise PostCommentException(400, "User must be specified")
        c = Comment(site=site.key, username=user, content=comment, url=url)
        c.put()
