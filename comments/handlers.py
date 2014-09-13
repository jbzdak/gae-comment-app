# -*- coding: utf-8 -*-
import json
from urlparse import urlparse
from comments.services import CommentService, PostCommentException

import jinja2
import webapp2

import main


def create_envioronment(debug):
    env = jinja2.Environment(
        loader=jinja2.PackageLoader("comments")
    )
    env.globals['debug'] = debug
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


class PostCommentRefferer(webapp2.RequestHandler):

    def soft_error(self, code, msg):
        self.response.clear()
        self.response.write(json.dumps({"status": code, "msg": msg}))

    def get(self):

        ref = self.request.headers.get('Referer')
        if ref is None:
            self.soft_error(400, "Referrer not set")
            return
        uri = urlparse(ref)
        sitedomain = uri.netloc
        try:
            comments = CommentService.posts_for_url(uri.path, sitedomain)
        except PostCommentException as e:
            self.soft_error(e.error_code, e.message)

        # It would probably be better to add Comment
        # Serialized to json so we don't hold comments
        # in memory.

        json_comments = [
            {
                "content": c.content,
                "username": c.username,
                "date": c.date.isoformat()
            }
            for c in comments
        ]

        json.dump(json_comments, self.response)

    def post(self):

        # TODO: Add some markup and sanitize input

        ref = self.request.headers.get('Referer')
        if ref is None:
            self.soft_error(400, "Referrer not set")
            return
        uri = urlparse(ref)
        sitedomain = uri.netloc
        post = self.request.POST
        try:
            CommentService.post_comment(
                user=post.get('username'),
                comment=post.get('comment'),
                domain=sitedomain,
                url=uri.path)
        except PostCommentException as e:
            self.soft_error(e.error_code, e.message)
            return
        self.response.write(json.dumps({"status": 201, "msg": "Created"}))


class PostCommentReferrerTestSubmit(webapp2.RequestHandler):

    def get(self):
        env = get_enviorment()
        tmpl = env.get_template("submit.html")
        stream = tmpl.stream()
        stream.dump(self.response)
