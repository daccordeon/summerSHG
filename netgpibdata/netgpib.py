import sys
#import math
import socket
import time
#import pdb
import select
import struct
import termstatus


class netGPIB:
    def __init__(self, ip, gpibAddr, eot=b'\004', debug=0,
                 auto=False, log=False, tSleep=0):

        # End of Transmission character
        self.eot = eot
        # EOT character number in the ASCII table
        self.eotNum = struct.unpack('B', eot)[0]

        # Debug flag
        self.debug = debug

        # Auto mode
        self.auto = auto

        # Waiting time
        self.tSleep = tSleep

        # Log mode
        self.log = log

        self.ip = ip
        self.gpibAddr = gpibAddr

        # Connect to the GPIB-Ethernet converter
        netAddr = (ip, 1234)
        self.netSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.netSock.connect(netAddr)

        # Initialize the GPIB-Ethernet converter
        self.netSock.setblocking(0)
        self.netSock.send(("++addr " + str(self.gpibAddr) + "\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++eos 3\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++mode 1\n").encode())
        time.sleep(0.1)
        if self.auto:
            self.netSock.send(("++auto 1\n").encode())
        else:
            self.netSock.send(("++auto 0\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++ifc\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++read_tmo_ms 3000\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++eot_char " + str(self.eotNum) + "\n").encode())
        self.netSock.send(("++eot_enable 1\n").encode())
        self.netSock.send(("++addr " + str(self.gpibAddr) + "\n").encode())

    def refresh(self):
        self.netSock.send(("++addr " + str(self.gpibAddr) + "\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++eos 3\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++mode 1\n").encode())
        time.sleep(0.1)
        if self.auto:
            self.netSock.send(("++auto 1\n").encode())
        else:
            self.netSock.send(("++auto 0\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++ifc\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++read_tmo_ms 3000\n").encode())
        time.sleep(0.1)
        self.netSock.send(("++eot_char" + str(self.eotNum) + "\n").encode())
        self.netSock.send(("++eot_enable 1\n").encode())
        self.netSock.send(("++addr " + str(self.gpibAddr) + "\n").encode())

    def getData(self, buf, sleep=None):
        if sleep is None:
            sleep = self.tSleep + 0.1

        data = ""
        dlen = 0
        if self.debug == True:
            progressInfo = termstatus.statusTxt("0 bytes received")
        while True:  # Repeat reading data until eot is found
            while True:  # Read some data
                readSock, writeSock, errSock = select.select(
                    [self.netSock], [], [], 3)
                if len(readSock) == 1:
                    data1 = readSock[0].recv(buf)
                    if self.debug == True:
                        dlen = dlen + len(data1)
                        progressInfo.update(str(dlen) + ' bytes received')
                    # Special character Handling
                    data1 = data1.replace(b'\xfb', b'rt')
                    data1 = data1.replace(b'\xfd', b'^2')
                    break
            # if eot is found at the end
            if data1.decode()[-1] == self.eot.decode():
                data = data + data1.decode()[:-1]  # remove eot
                break
            else:
                data = data + data1.decode()
                time.sleep(sleep)

        if self.debug == True:
            progressInfo.end()
        return data

    def query(self, string, buf=100, sleep=None):
        """Send a query to the device and return the result."""
        if sleep is None:
            sleep = self.tSleep
        if self.log:
            print("?? %s" % string, file=sys.stderr)
        self.netSock.send((string + "\n").encode())
        if not self.auto:
            time.sleep(sleep)
            self.netSock.send(("++read eoi\n").encode())  # Change to listening mode
        ret = self.getData(buf)
        if self.log:
            print("== %s" % ret.strip(), file=sys.stderr)
        return ret

    def srq(self):
        """Poll the device's SRQ"""
        self.netSock.send(("++srq\n").encode())
        while True:  # Read some data
            readSock, writeSock, errSock = select.select(
                [self.netSock], [], [], 3)
            if len(readSock) == 1:
                data = readSock[0].recv(100)
                break

        return data[:-2]

    def command(self, string, sleep=None):
        """Send a command to the device."""
        if sleep is None:
            sleep = self.tSleep
        if self.log:
            print(">> %s" % string, file=sys.stderr)
        self.netSock.send((string + "\n").encode())
        time.sleep(sleep)

    def spoll(self):
        """Perform a serial polling and return the result."""
        self.netSock.send(("++spoll\n").encode())
        while True:  # Read some data
            readSock, writeSock, errSock = select.select(
                [self.netSock], [], [], 3)
            if len(readSock) == 1:
                data = readSock[0].recv(100)
                break

        return data[:-2]

    def close(self):
        self.netSock.close()

    def setDebugMode(self, debugFlag):
        if debugFlag:
            self.debug = 1
        else:
            self.debug = 0


def gpibGetData(netSock, buf, eot, debug=0):
    data = ""
    while True:  # Repeat reading data until eot is found
        while True:  # Read some data
            readSock, writeSock, errSock = select.select([netSock], [], [], 3)
            if len(readSock) == 1:
                data1 = readSock[0].recv(buf)
                if debug == True:
                    print((str(len(data1)) + ' bytes received'))
                break

        if data1[len(data1) - 1] == eot:  # if eot is found at the end
            data = data + data1[0:len(data1) - 1]  # remove eot
            break
        else:
            data = data + data1
            time.sleep(1)

    return data
