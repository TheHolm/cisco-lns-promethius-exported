from pysnmp.hlapi import nextCmd, SnmpEngine, ContextData, ObjectType, ObjectIdentity, CommunityData, UdpTransportTarget
import http.server
import threading
import argparse
import time

HTTP_PORT_NUMBER = 8000

def get_l2tp_users(SNMP_target,auth_data,circuit_ids):
        thread_data = threading.local()
        print('Getting L2TP users...', flush=True)
        for (thread_data.errorIndication,
             thread_data.errorStatus,
             thread_data.errorIndex,
             thread_data.varBinds) in nextCmd(SnmpEngine(),
                                  auth_data,
                                  SNMP_target,
                                  ContextData(),
                                  ObjectType(ObjectIdentity('.1.3.6.1.4.1.9.10.24.1.3.2.1.2.2')),
                                  lexicographicMode=False):

            if thread_data.errorIndication:
                print(thread_data.errorIndication)
                break
            elif thread_data.errorStatus:
                print('%s at %s' % (thread_data.errorStatus.prettyPrint(),
                                    thread_data.errorIndex and thread_data.varBinds[int(thread_data.errorIndex) - 1][0] or '?'))
                break
            else:
                for thread_data.varBind in thread_data.varBinds:
                    thread_data.uid = str(thread_data.varBind[0]).split(".")
                    if str(thread_data.varBind[1]) != "":
                        circuit_ids[thread_data.uid[-2]+'.'+thread_data.uid[-1]] = str(thread_data.varBind[1])

        print(str(len(circuit_ids)) + ' users found')


def get_interface_ids(SNMP_target,auth_data,interface_IDs):
    thread_data = threading.local()
    print('Finding interface indexes...', flush=True)
    for (thread_data.errorIndication,
         thread_data.errorStatus,
         thread_data.errorIndex,
         thread_data.varBinds) in nextCmd(SnmpEngine(),
                              auth_data,
                              SNMP_target,
                              ContextData(),
                              ObjectType(ObjectIdentity('.1.3.6.1.4.1.9.10.24.1.3.2.1.11')),
                              lexicographicMode=False):

        if thread_data.errorIndication:
            print(thread_data.errorIndication)
            break
        elif thread_data.errorStatus:
            print('%s at %s' % (thread_data.errorStatus.prettyPrint(),
                                thread_data.errorIndex and thread_data.varBinds[int(thread_data.errorIndex) - 1][0] or '?'))
            break
        else:
            for thread_data.varBind in thread_data.varBinds:
                thread_data.uid = str(thread_data.varBind[0]).split(".")
                try:
                    interface_IDs[str(thread_data.varBind[1])] = thread_data.uid[-2]+'.'+thread_data.uid[-1]
                except KeyError:
                    pass

    print('Got Vi interface names  for ' + str(len(interface_IDs)) + ' interfaces')

def get_int_stats(SNMP_target,auth_data,interface_data,OID):
    print('Getting stats for OID: ',OID , flush=True)
    thread_data = threading.local()
    for (thread_data.errorIndication,
         thread_data.errorStatus,
         thread_data.errorIndex,
         thread_data.varBinds) in nextCmd(SnmpEngine(),
                              auth_data,
                              SNMP_target,
                              ContextData(),
                              ObjectType(ObjectIdentity(OID)),
                              # ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.6')), # (64 bit - but not supported by Cisco)
                              lexicographicMode=False):

        if thread_data.errorIndication:
            print(thread_data.errorIndication)
            break
        elif thread_data.errorStatus:
            print('%s at %s' % (thread_data.errorStatus.prettyPrint(),
                                thread_data.errorIndex and thread_data.varBinds[int(thread_data.errorIndex) - 1][0] or '?'))
            break
        else:
            for thread_data.varBind in thread_data.varBinds:
                thread_data.uid = str(thread_data.varBind[0]).split(".")
                try:
                    interface_data[thread_data.uid[-1]] = int(thread_data.varBind[1])
                except KeyError:
                    # print("Interface ID "+uid[-1]+" not found")
                    pass

    print('Got ' + str(len(interface_data)) + ' data entries for OID: ' + OID)

def get_usage(auth_data, SNMP_target):
    # launching threads to collect data.
    # if more indexes is requred it is good time to conver it to loop.

    circuit_ids = {}
    t1 = threading.Thread(target=get_l2tp_users, args=(SNMP_target,auth_data,circuit_ids))
    t1.start()

    interface_IDs = {}
    t2 = threading.Thread(target=get_interface_ids, args=(SNMP_target,auth_data,interface_IDs))
    t2.start()

    interface_RX_data = {}
    t3 = threading.Thread(target=get_int_stats, args=(SNMP_target,auth_data,interface_RX_data,'1.3.6.1.2.1.2.2.1.10'))
    t3.start()

    interface_TX_data = {}
    t4 = threading.Thread(target=get_int_stats, args=(SNMP_target,auth_data,interface_TX_data,'1.3.6.1.2.1.2.2.1.16'))
    t4.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()

    # print(next(iter(circuit_ids.items())),next(iter(interface_IDs.items())),next(iter(interface_RX_data.items())))

    print('Combining collected data')
    users_stats = {}
    for interface_ID in interface_IDs:
        try:
            users_stats[circuit_ids[interface_IDs[interface_ID]]] = {
            "RX_Octets" : interface_RX_data[interface_ID],
            "TX_Octets" : interface_TX_data[interface_ID]
            }
        except KeyError:
            pass  # some data missing for interface ID, just ignoring it

    print('Done')
    return(users_stats)
# end of get_usage(auth_data,SNMP_target)


class MyHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

    def _set_headers_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

    def do_GET(self):

        if "/?target=" not in self.path:
            self._set_headers_404()
            return()

        self._set_headers()
        dest_host = self.path.split('=')[1]
        print('Target: ',dest_host)

        start_time = time.monotonic()
        self.wfile.write("\n".encode('utf-8'))

        auth_data = CommunityData(SNMP_COMMUNITY, mpModel=0)
        SNMP_target = UdpTransportTarget((dest_host, SNMP_UDP_PORT))

        responce = "# TYPE ifOutOctets counter\n"
        users_stats = get_usage(auth_data, SNMP_target)
        for username in users_stats.keys():
            try:
                responce = responce + 'ifOutOctets{ user="' + username + '" } ' + str(users_stats[username]['TX_Octets']) + '\n'
            except KeyError:
                pass

        responce = responce + "# TYPE ifInOctets counter\n"
        for username in users_stats.keys():
            try:
                responce = responce + 'ifInOctets{ user="' + username + '" } ' + str(users_stats[username]['RX_Octets']) + '\n'
            except KeyError:
                pass

        responce = responce + '# TYPE total_l2tp_sessions summary\n'
        responce = responce + 'total_l2tp_sessions ' + str(len(users_stats)) + '\n'

        responce = responce + '# TYPE request_processing_seconds summary\n'
        responce = responce + 'request_processing_seconds ' + str(time.monotonic() - start_time) + '\n'

        self.wfile.write(responce.encode('utf-8'))
        self.wfile.write("\n".encode('utf-8'))

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers_404()
        return()
        self._set_headers()


# Promethius part
# users_stats = get_usage(auth_data,SNMP_target)

# HTTP_PORT_NUMBER

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Per-User traffic stats Pronethetius exporter for Cisco LNS.')
    parser.add_argument('-c', metavar='community', type=str,required=True,
                    help='SNMPv2 community string')
    parser.add_argument('-s', metavar='snmp_port', type=int, default=161,
                        help='SNMP destination UDP port, default 161')
    parser.add_argument('-p', metavar='http_port', type=int, default=8000,
                    help='HTTP port to listen for Promethius scrapper, default 8000')
    parser.add_argument('-i', metavar='bind_to_ip', type=str, default="",
                    help='IP address where HTTP server will listen, default all interfaces')
    args = vars(parser.parse_args())
    HTTP_PORT_NUMBER = args['p']
    HTTP_BIND_IP = args['i']
    SNMP_COMMUNITY = args['c']
    SNMP_UDP_PORT = args['s']
    print(str(args))
    # starting server
    server_class = MyHandler
    httpd = http.server.ThreadingHTTPServer((HTTP_BIND_IP, HTTP_PORT_NUMBER), server_class)
    print(time.asctime(), "Server Starts - %s:%s" % ("*" if HTTP_BIND_IP == '' else HTTP_BIND_IP, HTTP_PORT_NUMBER))
    httpd.serve_forever()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % ("localhost", HTTP_PORT_NUMBER))
