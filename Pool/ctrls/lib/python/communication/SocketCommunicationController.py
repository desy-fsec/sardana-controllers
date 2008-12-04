from pool import CommunicationController
import socket
import time
import array
from threading import Lock
import PyTango

class SocketComCtrl(CommunicationController):
    """A generic Sardana socket communication controller"""
    
    MaxDevice = 64

    ctrl_extra_attributes = {
       'Host'     : {'Type':'PyTango.DevString', 'R/W Type':'PyTango.READ_WRITE'},
       'Port'     : {'Type':'PyTango.DevLong',   'R/W Type':'PyTango.READ_WRITE'},
       'Timeout'  : {'Type':'PyTango.DevLong',   'R/W Type':'PyTango.READ_WRITE'}}

    def __init__(self,inst,props):
        CommunicationController.CommunicationController.__init__(self,inst,props)
        self.socket_data = self.MaxDevice*[None,]

    def AddDevice(self,ind):

        print "[SocketComCtrl]",self.inst_name,": In Adddevice for [",ind,"]"

        if ind > self.MaxDevice:
            raise Exception("Index (%d) device for this controller beyond max limit (%d) " % (ind,self.MaxDevice))

        sock = Socket()

        self.socket_data[ind-1] = sock

    def DeleteDevice(self,ind):
        self.socket_data[ind-1] = None

    def SetExtraAttributePar(self,ind,name,value):

        sk = self.socket_data[ind-1]

        if name == "Timeout":
            sk.settimeout(value)
        elif name == "Host":
            sk.sethost(value)
        elif name == "Port":
            sk.setport(value)

    def GetExtraAttributePar(self,ind,name):

        sk = self.socket_data[ind-1]

        if name == "Timeout":
            return int(sk.gettimeout())
        elif name == "Host":
            return sk.host
        elif name == "Port":
            return int(sk.port)

    def GetState(self,ind):
        print "[SocketComCtrl]",self.inst_name,"In GetState"

    def StateOne(self,ind):
        sk = self.socket_data[ind-1]
 
        if sk.connected == True:
            return (PyTango.DevState.ON,    "The socket is connected")
        elif sk.available == True:
            return (PyTango.DevState.OFF,   "The socket is closed")
        else:
            return (PyTango.DevState.FAULT, "The socket is fault")

    def SetPar(self,par,value):
        print "[SocketComCtrl] in SetPar" 
        return "tirolalira"
       
    def GetPar(self,par):
        print "[SocketComCtrl] in GetPar" 
        return "tirolalira"
       
    def OpenOne(self,ind):
        sk = self.socket_data[ind-1]
        sk.connect()

    def CloseOne(self,ind):
        sk = self.socket_data[ind-1]
        sk.disconnect()

    def ReadOne(self,ind,max_read_len):
        sk = self.socket_data[ind-1]
        return sk.recv(max_read_len)

    def WriteOne(self,ind,buf,write_len):

        sk = self.socket_data[ind-1]
        sk.send( buf )
        return write_len

    def WriteReadOne(self,ind,buf,write_len,max_read_len):

        sk   = self.socket_data[ind-1]
        data = sk.sendrecv( buf, max_read_len)
        #print "[SocketComCtrl] %s: WriteReadOne sends (%s), returns (%s)" % (self.inst_name,buf,data)
        return data

    def ReadLineOne(self,ind):
        sk = self.socket_data[ind-1]
        return sk.recv(-1)

    def SendToCtrl(self,in_data):
        pass

    def __del__(self):
        print "[SocketComCtrl]",self.inst_name,": Aarrrrrg, I am dying"


class Socket:
    def __init__(self):

         self.available = False
         self.connected = False
         self.timeout   = 1.0
         self.lock      = Lock()
         self.host      = None
         self.port      = None

         try:
            self.socket    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.available = True
         except:
            self.available = False

    def recv(self, readlen):
         # what if readlen == -1 ? how to get the number of available characters?
         readlen = 1024
         return self.socket.recv(readlen)

    def send(self, buf):
         #print "[Socket] Socket send (%s) \n" % buf
         self.socket.send(buf)

    def sendrecv(self, buf, readlen):

         self.flush()

         if readlen <= 0:
            readlen = 512

         time.sleep(0.1)
         #print "[Socket] sendrecv (readlen=%d) " % readlen

         self.lock.acquire()
         try:
            self.send(buf)
            time.sleep(0.1)
            data = self.recv(readlen)
         except Exception,msg:
            data = ""
            print "error sending/reading socket" 
            print msg
         finally:
            self.lock.release()
            return data
    
    def connect(self):
         # set timeout to something small 

         if self.checkhost() == -1:
             return

         if self.available == False:
             return

         #self.socket.settimeout(0.1)

         try:
             self.socket.connect((self.host,self.port))
             self.connected = True
         except socket.error, reason:
             self.connected = False
             print "Error connecting to socket. Error is: ", reason[1]
         #self.socket.settimeout(self.timeout)

    def disconnect(self):
         self.socket.close()
         self.connected = False

    def flush(self):
         return
         try:
           #self.socket.settimeout(0.1)
           bla = self.recv(512)
           if bla != "":
              print "[Socket] flush found had some crap (%s)" % bla
           #self.socket.settimeout(self.timeout)
         except socket.timeout:
           pass
         except:
           print "Flush failed"

    def gettimeout(self):
         return self.socket.gettimeout()
    
    def settimeout(self,timeout):
         print "[Socket] setting timeout %d" % timeout
         self.socket.settimeout(0.3)
         self.timeout = timeout

    def sethost(self, hostname):
         self.host = hostname

    def setport(self, portno):
         self.port = portno

    def checkhost(self):
         # check that hostname in DNS
         pass


if __name__ == "__main__":
    obj = SocketComCtrl('test',{'Sockets':['www.google.com:80']})

    obj.AddDevice(1)
    obj.DeleteDevice(1)
