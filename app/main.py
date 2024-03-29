#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import Crypto

import webapp2

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

from comments import handlers
from comments import admin_handlers


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')

routes = [
    ('/', MainHandler),
    ('/comment/', handlers.PostCommentRefferer),
    ('/admin/comment', admin_handlers.CommentAdmin),
    ('/admin/site/add', admin_handlers.AddSiteAdmin),
    (r'/admin/site/edit/([^/]+)', admin_handlers.EditSite),
    ('/admin/site/list', admin_handlers.ListSites),
]

if debug:
    routes.append(("/test/comment/", handlers.PostCommentReferrerTestSubmit))

app = webapp2.WSGIApplication(routes=routes, debug=debug)
