# -*- coding: utf-8 -*-
import json
from urlparse import urlparse
from comments.services import CommentService, PostCommentException

import jinja2
import webapp2



from env_utils import get_enviorment


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
        tmpl = env.get_template("admin/comment_admin.html")
        stream = tmpl.stream()
        stream.dump(self.response)
