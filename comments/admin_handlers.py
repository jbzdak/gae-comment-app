# -*- coding: utf-8 -*-
from google.appengine.ext.ndb.key import Key
from comments.db import Site
from comments.services import CommentService, NoSuchSiteException, SiteService
from google.appengine.ext import ndb

import jinja2
import webapp2

from env_utils import get_enviorment

from google.appengine.api import users


class CommentAdmin(webapp2.RequestHandler):

    def get_comments(self):
        user = users.get_current_user()
        if self.site_id:
            site = ndb.Key(urlsafe=self.site_id).get()
            SiteService.validate_can_moderate_site(site, user)
            sites = [site]
        else:
            sites = SiteService.sites_by_user(user)

        return CommentService.filter_posts(site=sites, state=self.state)

    def get(self):
        self.site_id = self.request.GET.get('site_id')
        self.state = self.request.GET.get('state')
        ctx = {
            "sites": SiteService.sites_by_user(users.get_current_user()),
            "comments": self.get_comments(),
            "selected_site": self.site_id,
            "selected_state": self.state
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


class AddSiteAdmin(webapp2.RequestHandler):

    def get(self):
        env = get_enviorment()
        tmpl = env.get_template("/admin/add_site.html")
        stream = tmpl.stream()
        stream.dump(self.response)

    def post(self):
        post = self.request.POST

        SiteService.create_site(
            post['siteurl'], post['sitename'],
            users.get_current_user(),
            post.getall('admin')
        )


class ListSites(webapp2.RequestHandler):

    def get(self):
        ctx = {
            "sites": SiteService.sites_by_user(
                users.get_current_user()
            )
        }
        env = get_enviorment()
        tmpl = env.get_template("/admin/list_sites.html")
        stream = tmpl.stream(**ctx)
        stream.dump(self.response)


class EditSite(webapp2.RequestHandler):

    def get(self, site_key):
        site = ndb.Key(urlsafe=site_key).get()
        ctx = {
            "s": site
        }
        env = get_enviorment()
        tmpl = env.get_template("/admin/add_site.html")
        stream = tmpl.stream(**ctx)
        stream.dump(self.response)

    def post(self, site_key):
        site = ndb.Key(urlsafe=site_key).get()
        post = self.request.POST
        SiteService.update_site(
            site,
            post['siteurl'], post['sitename'],
            users.get_current_user(),
            post.getall('admin')
        )
        self.response.location = '/admin/site/list'
        self.response.status = 303

