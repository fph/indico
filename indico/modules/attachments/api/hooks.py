# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.modules.events import Event
from indico.modules.attachments.api.util import build_folders_api_data
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.sessions import Session
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError


@HTTPAPIHook.register
class AttachmentsExportHook(HTTPAPIHook):
    TYPES = ('attachments',)
    RE = (r'(?P<event_id>\d+)'
          r'((/session/(?P<session_id>\d+)|(/contribution/(?P<contribution_id>\d+)(/(?P<subcontribution_id>\d+))?))?)?')
    MAX_RECORDS = {}
    GUEST_ALLOWED = True
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(AttachmentsExportHook, self)._getParams()
        event = self._obj = Event.get(self._pathParams['event_id'], is_deleted=False)
        if event is None:
            raise HTTPAPIError('No such event', 404)
        session_id = self._pathParams.get('session_id')
        if session_id:
            self._obj = Session.query.with_parent(event).filter_by(id=session_id).first()
            if self._obj is None:
                raise HTTPAPIError("No such session", 404)
        contribution_id = self._pathParams.get('contribution_id')
        if contribution_id:
            contribution = self._obj = Contribution.query.with_parent(event).filter_by(id=contribution_id).first()
            if contribution is None:
                raise HTTPAPIError("No such contribution", 404)
            subcontribution_id = self._pathParams.get('subcontribution_id')
            if subcontribution_id:
                self._obj = SubContribution.query.with_parent(contribution).filter_by(id=subcontribution_id).first()
                if self._obj is None:
                    raise HTTPAPIError("No such subcontribution", 404)

    def _hasAccess(self, aw):
        user = aw.getUser().user if aw.getUser() else None
        return self._obj.can_access(user)

    def export_attachments(self, aw):
        return {'folders': build_folders_api_data(self._obj)}
