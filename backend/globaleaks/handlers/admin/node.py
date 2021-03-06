# -*- coding: UTF-8
#
#   /admin/node
#   *****
# Implementation of the code executed on handler /admin/node
#
import os
from twisted.internet.defer import inlineCallbacks

from globaleaks import models, utils, LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import NodeFactory, PrivateFactory
from globaleaks.models.l10n import EnabledLanguage, NodeL10NFactory
from globaleaks.orm import transact, transact_ro
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log


def db_admin_serialize_node(store, language):
    node_dict = NodeFactory(store).admin_export()

    # Contexts and Receivers relationship
    configured  = store.find(models.ReceiverContext).count() > 0
    custom_homepage = os.path.isfile(os.path.join(GLSettings.static_path, "custom_homepage.html"))

    misc_dict = {
        'version': PrivateFactory(store).get_val('version'),
        'languages_supported': LANGUAGES_SUPPORTED,
        'languages_enabled': EnabledLanguage.get_all_strings(store),
        'configured': configured,
        'custom_homepage': custom_homepage,
    }

    l10n_dict = NodeL10NFactory(store).localized_dict(language)

    return utils.sets.disjoint_union(node_dict, misc_dict, l10n_dict)


@transact_ro
def admin_serialize_node(store, language):
    return db_admin_serialize_node(store, language)


def enable_disable_languages(store, request):
    cur_enabled_langs = EnabledLanguage.get_all_strings(store)
    new_enabled_langs = [unicode(y) for y in request['languages_enabled']]

    if len(new_enabled_langs) < 1:
        raise errors.InvalidInputFormat("No languages enabled!")

    if request['default_language'] not in new_enabled_langs:
        raise errors.InvalidInputFormat("Invalid lang code for chosen default_language")

    appdata = None
    for lang_code in new_enabled_langs:
        if lang_code not in LANGUAGES_SUPPORTED_CODES:
            raise errors.InvalidInputFormat("Invalid lang code: %s" % lang_code)
        if lang_code not in cur_enabled_langs:
            if appdata is None:
              appdata = load_appdata()
            log.debug("Adding a new lang %s" % lang_code)
            EnabledLanguage.add_new_lang(store, lang_code, appdata)

    for lang_code in cur_enabled_langs:
        if lang_code not in new_enabled_langs:
            EnabledLanguage.remove_old_lang(store, lang_code)


# TODO This cmd issues at least 3 SQL queries on node config.
def db_update_node(store, request, language):
    """
    Update and serialize the node infos

    :param store: the store on which perform queries.
    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the node
    """
    enable_disable_languages(store, request)

    node_l10n = NodeL10NFactory(store)
    node_l10n.update(request, language)

    node = NodeFactory(store)
    node.update(request)

    if request['basic_auth'] and request['basic_auth_username'] != '' and request['basic_auth_password']  != '':
        node.set_val('basic_auth', True)
        node.set_val('basic_auth_username', request['basic_auth_username'])
        node.set_val('basic_auth_password', request['basic_auth_password'])
    else:
        node.set_val('basic_auth', False)

    db_refresh_memory_variables(store)

    # TODO pass instance of db_update_node into admin_serialize
    return db_admin_serialize_node(store, language)


@transact
def update_node(*args):
    return db_update_node(*args)


class NodeInstance(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Get the node infos.

        Parameters: None
        Response: AdminNodeDesc
        """
        node_description = yield admin_serialize_node(self.request.language)
        self.write(node_description)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self):
        """
        Update the node infos.

        Request: AdminNodeDesc
        Response: AdminNodeDesc
        Errors: InvalidInputFormat
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminNodeDesc)

        node_description = yield update_node(request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(202) # Updated
        self.write(node_description)
