# -*- coding: utf-8 -*-
from comments.services import CommentService
from google.appengine.ext import ndb

import jinja2
import webapp2

from env_utils import get_enviorment


class CommentAdmin(webapp2.RequestHandler):

    def get_comments(self):
        return CommentService.filter_posts()

    def get(self):
        ctx = {
            "comments": self.get_comments()
        }
        env = get_enviorment()
        tmpl = env.get_template("/admin/comment_admin.html")
        stream = tmpl.stream(**ctx)
        stream.dump(self.response)

    def post(self):
        post = self.request.POST
        action = post['action']
        key = ndb.Key(urlsafe=post['key'])
        comment = key.get()
        if action == "set-state":
            state = post['new-state']
            CommentService.update_comment_state(comment, state)
        elif action == 'content':
            content = post['comment']
            CommentService.update_comment_contents(comment, content)
        else:
            raise ValueError("Invalid content")
        self.response.location = self.request.referer
        self.response.status=303
        # TODO: Due to eventual consistency(?) we get
        # coment that was updated last time doesn't get
        # new data when we render comment list.
        # If this persists on GAE we might need to do
        # something with it
