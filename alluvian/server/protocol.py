'''
This file is used to do setup the protocol negotiations for detecting different capabilities.
'''

import telnetlib
import alluvian.globals
import select

PROTO_NEGOTIATION_WAIT_TIME = 1
# custom defined characters.
TELOPT_MXP = b'['
TELOPT_TTYPE = b'\x18'
SEND = b'\x01'


class Protocol(object):

    @staticmethod
    def get_proto_response(pid: int) -> bytes:
        rlist, wlist, xlist = select.select([alluvian.globals.mud._clients[pid].socket],
                                            [],
                                            [],
                                            PROTO_NEGOTIATION_WAIT_TIME)

        if alluvian.globals.mud._clients[pid].socket not in rlist:
            print("Negotiation Time out")
            return b''
        else:
            return alluvian.globals.mud._clients[pid].socket.recv(4096)


    @staticmethod
    def send_do(pid: int, protocol: bytes) -> bytes:
        proto_query = bytearray(telnetlib.IAC + telnetlib.DO + protocol)
        alluvian.globals.mud.write_byte_array(pid, proto_query)
        return Protocol.get_proto_response(pid)

    @staticmethod
    def send_will(pid: int, protocol: bytes) -> bytes:
        proto_query = bytearray(telnetlib.IAC + telnetlib.WILL + protocol)
        alluvian.globals.mud.write_byte_array(pid, proto_query)
        return Protocol.get_proto_response(pid)

    @staticmethod
    def negotiate_mxp(pid: int) -> bool:
        """Negotiate MXP conection.  This procotocl doesn't specify specifically whether the server should send
        DO or WILL MXP to the client first.  Try both.
        """
        accept = bytearray(telnetlib.IAC + telnetlib.WILL + TELOPT_MXP)
        response = Protocol.send_do(pid, TELOPT_MXP)

        if response == accept:
            alluvian.globals.mud.send_message(pid, 'ok detected it1!')
            return True
        else:
            accept = bytearray(telnetlib.IAC + telnetlib.DO + TELOPT_MXP)
            response = Protocol.send_will(pid, TELOPT_MXP)
            if response == accept:
                alluvian.globals.mud.send_message(pid, 'ok detected it2!')
                return True

        alluvian.globals.mud.send_message(pid, 'Declined.')
        return False

    @staticmethod
    def start_mxp(pid: int) -> None:
        proto_query = bytearray(telnetlib.IAC +
                                telnetlib.SB +
                                TELOPT_MXP +
                                telnetlib.IAC +
                                telnetlib.SE)
        alluvian.globals.mud.write_byte_array(pid, proto_query)
        return

    @staticmethod
    def negotiate_ttype(pid: int) -> bool:
        accept = bytearray(telnetlib.IAC + telnetlib.WILL + TELOPT_TTYPE)
        response = Protocol.send_do(pid, TELOPT_TTYPE)
        if response == accept:
            alluvian.globals.mud.send_message(pid, 'ok detected it ttype!')
            proto_query = bytearray(telnetlib.IAC +
                                    telnetlib.SB +
                                    TELOPT_TTYPE +
                                    SEND +
                                    telnetlib.IAC +
                                    telnetlib.SE)
            alluvian.globals.mud.write_byte_array(pid, proto_query)
            r2 = Protocol.get_proto_response(pid)
            return r2
        else:
            alluvian.globals.mud.send_message(pid, 'Declined.')
            return False

