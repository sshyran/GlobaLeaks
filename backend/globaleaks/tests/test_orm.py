from twisted.internet.defer import inlineCallbacks
from storm import exceptions

from globaleaks.tests import helpers

from globaleaks.orm import transact, transact_ro
from globaleaks.models import *
from globaleaks.utils.utility import datetime_null


class TestORM(helpers.TestGL):
    initialize_test_database_using_archived_db = False

    @transact
    def _transaction_with_exception(self, store):
        raise Exception

    @transact
    def _transaction_pragmas(self, store):
        # Verify setting enabled in the sqlite db
        self.assertEqual(store.execute("PRAGMA foreign_keys").get_one()[0], 1)  # ON
        self.assertEqual(store.execute("PRAGMA secure_delete").get_one()[0], 1) # ON
        self.assertEqual(store.execute("PRAGMA auto_vacuum").get_one()[0], 1)   # FULL

    @transact
    def _transaction_with_commit_close(self, store):
        store.commit()
        store.close()

    @transact
    def _transact_with_stuff(self, store):
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')
        receiver_user = User(self.dummyReceiverUser_1)
        receiver_user.password = self.dummyReceiverUser_1['password']
        receiver_user.salt = self.dummyReceiverUser_1['salt']
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']
        receiver_user.password_change_needed = self.dummyReceiverUser_1['password_change_needed']
        receiver_user.password_change_date = datetime_null()
        receiver_user.mail_address = self.dummyReceiverUser_1['mail_address']

        # Avoid receivers with the same username!
        receiver_user.username = unicode("xxx")

        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user_id = receiver_user.id
        store.add(receiver)

        # Set receiver.id = receiver.user.username = receiver_user.id
        receiver.id = receiver_user.username = receiver_user.id

        return receiver.id

    @transact
    def _transact_with_stuff_failing(self, store):
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')
        receiver_user = User(self.dummyReceiverUser_1)
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']
        receiver_user.password_change_needed = self.dummyReceiverUser_1['password_change_needed']
        receiver_user.password_change_date = datetime_null()
        receiver_user.mail_address = self.dummyReceiverUser_1['mail_address']
        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user_id = receiver_user.id
        store.add(receiver)

        raise exceptions.DisconnectionError

    @transact_ro
    def _transact_ro_add_mail(self, store):
        m = Mail({
            'address': 'evilaliv3@globaleaks.org',
            'subject': '',
            'body': ''
        })
        store.add(m)
        return m.id

    @inlineCallbacks
    def test_transaction_with_exception(self):
        yield self.assertFailure(self._transaction_with_exception(), Exception)

    def test_transaction_pragmas(self):
        return self._transaction_pragmas()

    def test_transaction_with_commit_close(self):
        return self._transaction_with_commit_close()

    @inlineCallbacks
    def test_transact_with_stuff(self):
        receiver_id = yield self._transact_with_stuff()
        # now check data actually written
        store = transact.get_store()
        self.assertEqual(store.find(Receiver, Receiver.id == receiver_id).count(), 1)

    @inlineCallbacks
    def test_transact_with_stuff_failing(self):
        receiver_id = yield self._transact_with_stuff_failing()
        store = transact.get_store()
        self.assertEqual(list(store.find(Receiver, Receiver.id == receiver_id)), [])

    @inlineCallbacks
    def test_transact_decorate_function(self):
        @transact
        def transaction(store):
            self.assertTrue(getattr(store, 'find'))

        yield transaction()

    @transact_ro
    def _transact_ro_check_mail_not_exists(self, store, mail_id):
        self.assertEqual(store.find(Mail, Mail.id == mail_id).one(), None)

    @inlineCallbacks
    def test_transact_ro(self):
        created_id = yield self._transact_ro_add_mail()
        yield self._transact_ro_check_mail_not_exists(created_id)
