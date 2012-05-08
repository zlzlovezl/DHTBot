import pickle
import StringIO

from twisted.web import xmlrpc, server
from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.python.monkey import MonkeyPatcher

from dhtbot import xml_rpc_client, constants
from dhtbot.xml_rpc_client import KRPC_Sender_Client, KRPC_Responder_Client
from dhtbot.krpc_types import Query

monkey_patcher = MonkeyPatcher()

class HollowXMLRPCServer(object):

    def __init__(self, url):
        pass

    def sendQuery(self, pickled_query, address, timeout):
        self.pickled_query = pickled_query
        self.address = address
        self.timeout = timeout
        # We pass back a valid pickled response
        input = StringIO.StringIO(pickled_query)
        query = pickle.load(input)
        response = query.build_response()
        response._queried = 11111
        output = StringIO.StringIO()
        pickle.dump(response, output)
        return output.getvalue()
    
    def ping(self, address, timeout=constants.rpctimeout):
        """
        Pass through all non-default arguments
        """
        args = [address]
        if timeout != constants.rpctimeout:
            args.append(timeout)
        return args

    def find_node(self, address, target_id, timeout=constants.rpctimeout):
        """
        Pass through all non-default arguments
        """
        args = [address, target_id]
        if timeout != constants.rpctimeout:
            args.append(timeout)
        return args

    def get_peers(self, address, target_id, timeout=constants.rpctimeout):
        """
        Pass through all non-default arguments
        """
        args = [address, target_id]
        if timeout != constants.rpctimeout:
            args.append(timeout)
        return args

    def announce_peer(self, address, port, token, timeout=constants.rpctimeout):
        """
        Pass through all non-default arguments
        """
        args = [address, port, token]
        if timeout != constants.rpctimeout:
            args.append(timeout)
        return args

    def _valid_sendQuery_arguments(self, query, address, timeout):
        """
        Verify that the client arguments transmit to the server succesfully

        After checking, this function will erase the recorded arguments
        (so the upcoming calls do not make mistakes)

        @returns Boolean indicating whether the arguments transmitted properly

        """
        output = StringIO.StringIO()
        pickle.dump(query, output)
        pickled_query = output.getvalue()
        equal = (pickled_query == self.pickled_query and
                 address == self.address and
                 timeout == self.timeout)
        self.pickled_query = None
        self.address = None
        self.timeout = None
        return equal

class ClientTestBase(object):
    """
    Ensure the client passes valid arguments to the server
    """

    test_address = ("127.0.0.1", 58585)
    test_timeout = 15

    def setUp(self):
        monkey_patcher.addPatch(xml_rpc_client.xmlrpclib,
                                "Server", HollowXMLRPCServer)
        monkey_patcher.patch()
        # Empty string is ok, since we monkey patched
        # over the xmlrpclib.Server
        self.kclient = KRPC_Sender_Client("")

    def tearDown(self):
        monkey_patcher.restore()

class KRPC_Sender_Client_TestCase(ClientTestBase, unittest.TestCase):
    def test_sendQuery_arguments(self):
        query = Query()
        query.rpctype = "ping"
        query._querier = 1515
        query._transaction_id = 636363
        _ignored = self.kclient.sendQuery(query,
                            self.test_address, self.test_timeout)
        self.assertTrue(self.kclient.server._valid_sendQuery_arguments(
                        query, self.test_address, self.test_timeout))

class KRPC_Responder_Client_TestCase(ClientTestBase, unittest.TestCase):

    test_target_id = 42

    def setUp(self):
        ClientTestBase.setUp(self)
        self.kclient = KRPC_Responder_Client("")

    def test_ping_argumentsNonDefaultTimeout(self):
        args = [self.test_address, self.test_timeout]
        passed_args = self.kclient.ping(*args)
        self.assertEquals(args, passed_args)

    def test_ping_argumentsDefaultTimeout(self):
        args = [self.test_address]
        passed_args = self.kclient.ping(*args)
        self.assertEquals(args, passed_args)

    def test_find_node_argumentsNonDefaultTimeout(self):
        args = [self.test_address, self.test_target_id, self.test_timeout]
        passed_args = self.kclient.find_node(*args)
        self.assertEquals(args, passed_args)

    def test_find_node_argumentsDefaultTimeout(self):
        args = [self.test_address, self.test_target_id]
        passed_args = self.kclient.find_node(*args)
        self.assertEquals(args, passed_args)