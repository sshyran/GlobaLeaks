# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import export
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.tests import helpers

class TestExportHandler(helpers.TestHandlerWithPopulatedDB):
    complex_field_population = True
    _handler = export.ExportHandler

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()
        yield DeliverySchedule().operation()

    @inlineCallbacks
    def test_export(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request({}, role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            # As the handler calls internally the flush() we should
            # mock that function because during tests the flush could not
            # be called as the handler is not fully run.
            def flush_mock():
                pass

            handler.flush = flush_mock

            yield handler.get(rtip_desc['id'])
