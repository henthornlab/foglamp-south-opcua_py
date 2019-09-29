# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

"""OPC UA South Plugin using the FreeOPCUA Python OPC UA Library"""
import copy
import os
import logging
import time
import asyncio
import uuid
import json
from threading import Thread


from foglamp.common import logger
from foglamp.plugins.common import utils
import async_ingest

from opcua import Client, Node

__author__ = "David Henthorn, Rose-Hulman Institute of Technology"
__copyright__ = "Copyright (c) 2019"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.INFO)
c_callback = None
c_ingest_ref = None
loop = None
t = None

_CONFIG_CATEGORY_NAME = 'OPCUA_PY'
_CONFIG_CATEGORY_DESCRIPTION = 'South Plugin OPC UA in Python'
_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'OPC UA South Plugin in Python',
        'type': 'string',
        'default': 'opcua_py',
        'readonly': 'true'
    },
    'url': {
        'description': 'OPC UA server connection string (opc.tcp)',
        'type': 'string',
        'default': 'opc.tcp://historian.local:9409/DvOPC',
        'order': '1',
        'displayName': 'Host'
    },
    'userName': {
        'description': 'User name, if needed (leave blank if unused)',
        'type': 'string',
        'default': '',
        'order': '2',
        'displayName': 'User Name'
    },
    'password': {
        'description': 'Password (leave blank if unused)',
        'type': 'string',
        'default': '',
        'order': '3',
        'displayName': 'Password'
    },
    'assetNamePrefix': {
        'description': 'Asset name prefix',
        'type': 'string',
        'default': 'opcua-',
        'order': '4',
        'displayName': 'Asset Name Prefix'
    },
    'subscriptions': {
        'description': 'JSON list of nodes to subscribe to',
        'type': 'JSON',
        'order': '5',
        'displayName': 'OPC UA Nodes to monitor through subscriptions',
        'default' : '{ "subscriptions" : [ "ns=2;s=0:FIT-321.CV", "ns=2;s=0:TE200-07/AI1/OUT.CV", "ns=2;s=0:TE200-12/AI1/OUT.CV" ] }'
    }
}


def plugin_info():
    """ Returns information about the plugin.
    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'opcua_py plugin',
        'version': '1.7.0',
        'mode': 'async',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.
    Args:
        config: JSON configuration document for the South plugin configuration category
    Returns:
        data: JSON object to be used in future calls to the plugin
    Raises:
    """
    handle = copy.deepcopy(config)
    return handle

def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    """
    _LOGGER.info("opcua_py: Old config for {} \n new config {}".format(handle, new_config))

    # plugin_shutdown
    plugin_shutdown(handle)

    # plugin_init
    new_handle = plugin_init(new_config)

    # plugin_start
    plugin_start(new_handle)

    return new_handle

def plugin_start(handle):
    global loop, t
    _LOGGER.info("opcua_py plugin_start called")

    url = handle['url']['value']
    userName = handle['userName']['value']
    password = handle['password']['value']

    _LOGGER.info('opcua_py: Attempting to connect to %s', url)

    client = Client(url=url)

    if userName:
        _LOGGER.info('opcua_py: Attempting to connect to OPC UA server with username and password.')
        _LOGGER.info('Username is %s with length %d', userName, len(userName))
        client.set_user(userName)
        client.set_password(password)
    else:
        _LOGGER.info('opcua_py: Attempting to connect with anonymously to OPC UA server.')

    client.connect()

    #Need to add some error checking on the connection

    subs = json.loads(handle['subscriptions']['value'])

    subs = subs["subscriptions"]
    _LOGGER.info('opcua_py: Attempting to subscribe to %s', subs)

    nodes = []

    for sub in subs:
        nodes.append(client.get_node(sub))

    handler = SubscriptionHandler()
    # We create a Client Subscription.
    subscription = client.create_subscription(500, handler)

    # We subscribe to data changes for our nodes (variables).
    subscription.subscribe_data_change(nodes)


    def run():
            global loop
            loop.run_forever()


    t = Thread(target=run)

    t.start()


def _plugin_stop(handle):
    _LOGGER.info('opcua_py: Stopping OPCUA Python plugin.')
    global loop
    loop.stop()

def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the South plugin service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        plugin shutdown
    """
    global client
    global subscription
    global _LOGGER
    global _callback_event_loop

    subscription.unsubscribe(nodes)
    subscription.delete()
    client.disconnect()

    _plugin_stop(handle)
    _LOGGER.info('opcua_py has shut down.')


def plugin_register_ingest(handle, callback, ingest_ref):
    """Required plugin interface component to communicate to South C server

    Args:
        handle: handle returned by the plugin initialisation call
        callback: C opaque object required to passed back to C->ingest method
        ingest_ref: C opaque object required to passed back to C->ingest method
    """
    global c_callback, c_ingest_ref
    c_callback = callback
    c_ingest_ref = ingest_ref


class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def datachange_notification(self, node: Node, val, data):
        """
        Callback for OPC UA Subscription.
        This method will be called when the Client received a data change message from the Server.
        """

        time_stamp = utils.local_timestamp()
        asset_name = str(node)
        #Trim the string to start with ns=
        ns_start = asset_name.find('ns=')
        if ns_start != -1:
             asset_name = asset_name[ns_start:]

        #Some OPC UA servers add extra parentheses, so remove them
        #Remove any extraneous parentheses
        asset_name = asset_name.replace("(","")
        asset_name = asset_name.replace(")","")

        #_LOGGER.info('opcua_py: datachange_notification %r %s', asset_name, val)
        key = str(uuid.uuid4())

        data = {
                'asset': asset_name,
                'timestamp': time_stamp,  # metric.timestamp
                'key' : key,
                'readings': {"value": val}
        } 

        async_ingest.ingest_callback(c_callback, c_ingest_ref, data)
