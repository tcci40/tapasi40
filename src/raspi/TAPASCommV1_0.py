#!/usr/bin/env python3
###################################################################################################
## SDI TAPAS python demo application - communication module
## 
## Revisions:
## 1.0 - Initial version
## 
## Copyright (c) 2017 Siemens AG
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions 
# are met:
#
# 1. Redistributions of source code must retain the above copyright 
#    notice, this list of conditions and the following disclaimer. 
#
# 2. Redistributions in binary form must reproduce the above copyright   
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of 
#    its contributors may be used to endorse or promote products derived 
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, 
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###################################################################################################

# module for platform check
import platform
                     
# module for data handling
import struct

#import pprint
#from collections import namedtuple
#import OLogging
import logging
import time

logger=logging.getLogger(__name__)
SPICLOCKFREQ_HZ=400*1000

# global variable necessary for crc-calculation
crc_table = [0] * 256

# used for crc
POLY = 0x1021
START = 0xFFFF
###
if (platform.machine() == "i586"):
    # this is necessary to run the script on IOT2000
    # (manual control of the CS-pin)
    #set filename for set_chipselect
    CS = "/sys/class/gpio/gpio10/value"

#function for setting chipselect, necessary only on IOT2000
def set_chipselect (status):
    file = open(CS, 'w')

    if(status == 0):
        file.write("0")
    elif(status == 1):
        file.write("1")
    else:
        file.write("0")

    file.close()
###

def GenerateCrcTable():
	logger.debug('Starting CRC table generation')
	for i in range(0, 256, 1):
		crc = i << 8
		for j in range(0, 8, 1):
			if crc & 0x8000:
				crc <<= 1
				crc = crc ^ POLY 
			else:
				crc <<= 1
		crc_table[i] = crc & 0xFFFF # just regard the lower 16Bit of the value
	logger.debug('Finished CRC table generation')

def CalcCrc(data, len_words):
	crc = START
	for i in range(0, len_words, 1):
		octet = data[i] & 0xFF

		idx = ((crc >> 8) & 0xFF) ^ octet
		crc = (crc << 8) ^ crc_table[idx]
		
		octet = (data[i] >> 8) & 0xFF
		idx = ((crc >> 8) & 0xFF) ^ octet
		crc = (crc << 8) ^ crc_table[idx]
	crc = crc & 0xFFFF # just regard the lower 16Bit of the value
	return crc

def getZeroMasterTxDict():
    master_tx_dict={};
    master_tx_dict["flags"] = 0 #resp_readable[0]
    master_tx_dict["i_Motor_numPolePairs"] = 0 #resp_readable[1]
    master_tx_dict["f_Motor_ratedCurrent"] = 0.0 #resp_readable[2]
    master_tx_dict["f_Motor_RoverLestFrequencyHz"] = 0.0 # resp_readable[3]
    master_tx_dict["f_Motor_fluxEstFrequency"] = 0.0 # resp_readable[4]
    master_tx_dict["f_CTRL_setpoint_speed"] = 0.0 # resp_readable[5]
    master_tx_dict["f_CTRL_setpoint_accel"] = 0.0 # resp_readable[6]
    master_tx_dict["f_resFloat0"] = 0.0 # resp_readable[7]
    master_tx_dict["f_resFloat1"] = 0.0 # resp_readable[8]
    master_tx_dict["f_resFloat2"] = 0.0 # resp_readable[9]
    master_tx_dict["f_resFloat3"] = 0.0 # resp_readable[10]
    master_tx_dict["f_resFloat4"] = 0.0 # resp_readable[11]
    master_tx_dict["f_resFloat5"] = 0.0 # resp_readable[12]
    master_tx_dict["f_resFloat6"] = 0.0 # resp_readable[13]
    master_tx_dict["f_resFloat7"] = 0.0 # resp_readable[14]
    master_tx_dict["f_resFloat8"] = 0.0 # resp_readable[15]
    master_tx_dict["f_resFloat9"] = 0.0 # resp_readable[16]
    master_tx_dict["f_resFloat10"] = 0.0 # resp_readable[17]
    master_tx_dict["u_STATUS_DOUT"] = 0 #resp_readable[18]
    master_tx_dict["u_reserved2"] = 0 #resp_readable[19]
    master_tx_dict["u_reserved3"] = 0 #resp_readable[20]
    master_tx_dict["CRC"] = 0 #resp_readable[21]
    return master_tx_dict

def getNeutralMasterTxDict():
    master_tx_dict=getZeroMasterTxDict()
    master_tx_dict["i_Motor_numPolePairs"] = 1
    master_tx_dict["f_Motor_RoverLestFrequencyHz"] = 10.0 # resp_readable[3]
    master_tx_dict["f_Motor_fluxEstFrequency"] = 10.0 # resp_readable[4]
    return master_tx_dict


def transferMasterSlave( spi
                    , flags=0
                    , numPolePairs=0
                    , ratedCurrent=0.0
                    , RoverLestFrequency=10.0
                    , fluxEstFrequency=10.0
                    , setpointSpeed=0.0
                    , setpointAccel=0.0
                    , f_resFloat0=0.0
                    , f_resFloat1=0.0
                    , f_resFloat2=0.0
                    , f_resFloat3=0.0
                    , f_resFloat4=0.0
                    , f_resFloat5=0.0
                    , f_resFloat6=0.0
                    , f_resFloat7=0.0
                    , f_resFloat8=0.0
                    , f_resFloat9=0.0
                    , f_resFloat10=0.0
                    , u_STATUS_DOUT=0
                    , u_reserved2=0
                    , u_reserved3=0
                    , u_CRC=0
                    ):
    master_tx_dict = getZeroMasterTxDict()
    master_tx_dict["flags"]                         = flags             
    master_tx_dict["i_Motor_numPolePairs"]          = numPolePairs      
    master_tx_dict["f_Motor_ratedCurrent"]          = ratedCurrent      
    master_tx_dict["f_Motor_RoverLestFrequencyHz"]  = RoverLestFrequency
    master_tx_dict["f_Motor_fluxEstFrequency"]      = fluxEstFrequency  
    master_tx_dict["f_CTRL_setpoint_speed"]         = setpointSpeed     
    master_tx_dict["f_CTRL_setpoint_accel"]         = setpointAccel     
    master_tx_dict["f_resFloat0"]                   = f_resFloat0       
    master_tx_dict["f_resFloat1"]                   = f_resFloat1       
    master_tx_dict["f_resFloat2"]                   = f_resFloat2       
    master_tx_dict["f_resFloat3"]                   = f_resFloat3       
    master_tx_dict["f_resFloat4"]                   = f_resFloat4       
    master_tx_dict["f_resFloat5"]                   = f_resFloat5       
    master_tx_dict["f_resFloat6"]                   = f_resFloat6       
    master_tx_dict["f_resFloat7"]                   = f_resFloat7       
    master_tx_dict["f_resFloat8"]                   = f_resFloat8       
    master_tx_dict["f_resFloat9"]                   = f_resFloat9       
    master_tx_dict["f_resFloat10"]                  = f_resFloat10      
    master_tx_dict["u_STATUS_DOUT"]                 = u_STATUS_DOUT     
    master_tx_dict["u_reserved2"]                   = u_reserved2       
    master_tx_dict["u_reserved3"]                   = u_reserved3       
    master_tx_dict["CRC"]                           = u_CRC             
   
    return commMasterSlave(spi, master_tx_dict)

def commMasterSlave(spi
                  , master_tx_dict = getNeutralMasterTxDict()
                  , structpackfmtMO = "HHffffffffffffffffHHHH"
                  , structpackfmtSO = "HHffffHHfffffffffffHHHH"
                  ):
    logger.info('MO pack fmt: {Mfmt:s} wordlength: {Mlen}) SO pack fmt: {Sfmt:s} wordlength: {Slen}'
                 .format(Mfmt = structpackfmtMO, Mlen = struct.calcsize(structpackfmtMO)
                       , Sfmt = structpackfmtSO, Slen = struct.calcsize(structpackfmtSO))
                )
    logger.debug('master_tx dict ---> {dict:r}'.format(master_tx_dict))
    # pprint.pprint(master_tx_dict)
    # packing data together
    sender_temp = struct.pack(structpackfmtMO, master_tx_dict["flags"]
                                             , master_tx_dict["i_Motor_numPolePairs"]
                                             , master_tx_dict["f_Motor_ratedCurrent"]
                                             , master_tx_dict["f_Motor_RoverLestFrequencyHz"]
                                             , master_tx_dict["f_Motor_fluxEstFrequency"]
                                             , master_tx_dict["f_CTRL_setpoint_speed"]
                                             , master_tx_dict["f_CTRL_setpoint_accel"]
                                             , master_tx_dict["f_resFloat0"]
                                             , master_tx_dict["f_resFloat1"]
                                             , master_tx_dict["f_resFloat2"]
                                             , master_tx_dict["f_resFloat3"]
                                             , master_tx_dict["f_resFloat4"]
                                             , master_tx_dict["f_resFloat5"]
                                             , master_tx_dict["f_resFloat6"]
                                             , master_tx_dict["f_resFloat7"]
                                             , master_tx_dict["f_resFloat8"]
                                             , master_tx_dict["f_resFloat9"]
                                             , master_tx_dict["f_resFloat10"]
                                             , master_tx_dict["u_STATUS_DOUT"]
                                             , master_tx_dict["u_reserved2"]
                                             , master_tx_dict["u_reserved3"]
                                             , master_tx_dict["CRC"]
                                             ) 
    print ("s_tuple: %s" % repr(struct.unpack(structpackfmtMO, sender_temp)))
    
    ret, r_CRC_ok=xferSPI(spi, sender_temp)

    resp_readable = struct.unpack(structpackfmtSO, ret)
    print ("r_tuple: %s" % repr(resp_readable))

    slave_rx_dict = {}
    slave_rx_dict["flags"] = resp_readable[0]
    slave_rx_dict["Protection mode"] = resp_readable[1]
    slave_rx_dict["dc-bus voltage"] = resp_readable[2]
    slave_rx_dict["dc-bus current"] = resp_readable[3]
    slave_rx_dict["board-temperature"] = resp_readable[4]
    slave_rx_dict["motor speed"] = resp_readable[5]
    slave_rx_dict["controller state [CTRL_state]"] = resp_readable[6]
    slave_rx_dict["estimator state [EST_state]"] = resp_readable[7]
    slave_rx_dict["motorRs"] = resp_readable[8]
    slave_rx_dict["motorRr"] = resp_readable[9]
    slave_rx_dict["motorLsd"] = resp_readable[10]
    slave_rx_dict["motorLsq"] = resp_readable[11]
    slave_rx_dict["ratedFlux"] = resp_readable[12]
    slave_rx_dict["analog in 0 voltage"] = resp_readable[13]
    slave_rx_dict["analog in 1 voltage"] = resp_readable[14]
    slave_rx_dict["analog in 2 voltage"] = resp_readable[15]
    slave_rx_dict["analog in 3 voltage"] = resp_readable[16]
    slave_rx_dict["analog in 4 voltage"] = resp_readable[17]
    slave_rx_dict["analog in 5 voltage"] = resp_readable[18]
    slave_rx_dict["status digital inputs"] = resp_readable[19]
    slave_rx_dict["spiStatus"] = resp_readable[20]
    slave_rx_dict["reserved2"] = resp_readable[21]
    slave_rx_dict["CRC"] = resp_readable[22]
    slave_rx_dict["r_CRC_ok"] = r_CRC_ok

    pprint.pprint(slave_rx_dict)
    return slave_rx_dict

def getZeroCoCoMODict():
    master_tx_dict={};
    master_tx_dict["flags"] = 0
    master_tx_dict["u_msgseq"] = 0
    master_tx_dict["f_Coil_setCurrent1"] = 0.0 
    master_tx_dict["f_Coil_setCurrent2"] = 0.0 
    master_tx_dict["f_Coil_setCurrent3"] = 0.0 
    master_tx_dict["f_Coil_setCurrent4"] = 0.0
    master_tx_dict["f_Coil_setCurrent5"] = 0.0
    master_tx_dict["f_Coil_setCurrent6"] = 0.0
    master_tx_dict["u_STATUS_DOUT"] = 0
    master_tx_dict["CRC"] = 0
#    master_tx_dict["u_reserved1"] = 0xff
#    master_tx_dict["u_reserved2"] = 0
#    print("sizeof(CoCoMODict): %i" % struct.calcsize("HHffffffHH"))
    return master_tx_dict

def getZeroCoCoSODict():
    slave_tx_dict={};
    slave_tx_dict["flags"] = 0
    slave_tx_dict["u_msgseq"] = 0
    slave_tx_dict["u_STATUS_statusErr"] = 0
    slave_tx_dict["spiStatus"] = 0

    slave_tx_dict["f_STATUS_boardTemp"] = 0.0 
    slave_tx_dict["f_STATUS_UdcBus"] = 0.0 
    slave_tx_dict["f_STATUS_IdcBus"] = 0.0 
    
    slave_tx_dict["f_Coil_Current1"] = 0.0 
    slave_tx_dict["f_Coil_Current2"] = 0.0 
#    slave_tx_dict["f_Coil_Current3"] = 0.0 
#    slave_tx_dict["f_Coil_Current4"] = 0.0
#    slave_tx_dict["f_Coil_Current5"] = 0.0
#    slave_tx_dict["f_Coil_Current6"] = 0.0
    slave_tx_dict["u_STATUS_DIN"] = 0
    slave_tx_dict["CRC"] = 0
#    slave_tx_dict["u_reserved1"] = 0xff
#    slave_tx_dict["u_reserved2"] = 0
#    print("sizeof(CoCoSODict): %i" % struct.calcsize("HHHHfffffHH"))
    return slave_tx_dict


def xferCoilCommunication(spi, coiltxdict = getZeroCoCoMODict()
                             , structpackfmtMO = "HHffffffHH"
                             , structpackfmtSO = "HHHHfffffHH"
                         ):
    logger.info('s_SPIMO pack fmt: ({Mfmt:s}) wordlength: {Mlen}, SO pack fmt: ({Sfmt:s}) wordlength: {Slen}'
                 .format(Mfmt = structpackfmtMO, Mlen = struct.calcsize(structpackfmtMO)
                       , Sfmt = structpackfmtSO, Slen = struct.calcsize(structpackfmtSO))
                )
    logger.debug('s_SPIMO dict ---> {txdict}'.format(txdict = coiltxdict))
    # packing data together
    sender_temp = struct.pack(structpackfmtMO, coiltxdict["flags"]
                                           , coiltxdict["u_msgseq"]
                                           , coiltxdict["f_Coil_setCurrent1"]
                                           , coiltxdict["f_Coil_setCurrent2"]
                                           , coiltxdict["f_Coil_setCurrent3"]
                                           , coiltxdict["f_Coil_setCurrent4"]
                                           , coiltxdict["f_Coil_setCurrent5"]
                                           , coiltxdict["f_Coil_setCurrent6"]
                                           , coiltxdict["u_STATUS_DOUT"]
                                           , coiltxdict["CRC"]
                             )
    if __debug__:
        logger.debug('s_SPIMO packed: {pack}'.format(pack = struct.unpack(structpackfmtMO, sender_temp)))
    
    ret, r_CRC_ok=xferSPI(spi, sender_temp)

    resp_readable = struct.unpack(structpackfmtSO, ret)
    logger.info('r_CRC_ok: {crcok}'.format(crcok = r_CRC_ok))
    if __debug__:
        logger.debug('r_SPISO: {pack}'.format(pack = resp_readable))

    coilrxdict = {}
    coilrxdict["flags"]=resp_readable[0]
    coilrxdict["u_msgseq"]=resp_readable[1]
    coilrxdict["u_STATUS_statusErr"] = resp_readable[2]
    coilrxdict["spiStatus"]=resp_readable[3]
    
    coilrxdict["f_STATUS_boardTemp"] = resp_readable[4]
    coilrxdict["f_STATUS_UdcBus"] = resp_readable[5]
    coilrxdict["f_STATUS_IdcBus"] = resp_readable[6]

    coilrxdict["f_Coil_Current1"]=resp_readable[7]
    coilrxdict["f_Coil_Current2"]=resp_readable[8]

    coilrxdict["u_STATUS_DIN"]=resp_readable[9]
    coilrxdict["CRC"]=resp_readable[10]
    coilrxdict["r_CRC_ok"]=r_CRC_ok
    logger.debug('r_SPISO dict ---> {rxdict}'.format(rxdict = coilrxdict))

    return coilrxdict


def xferSPI (spi, txwords):
    sender = []
    sender16 = []
    # first create a list containing all the single Bytes 
    for byte in txwords:
        sender.append(byte)

    # then create a second list which holds 16Bit values and the bytes swapped
    for i in range(0, len(sender), 2):
        temp = (sender[i+1]<<8) | (sender[i] )
        sender16.append(temp)

    # calculate the checksum for the "package" to be sent   
    send_CRC = CalcCrc(sender16, ((len(sender)//2)-1))
    packed_CRC = struct.pack('H', send_CRC)
    # now, add the Checksum to the package to be sent 
    sender[len(sender)-2] = packed_CRC[0]
    sender[len(sender)-1] = packed_CRC[1]
    
    sent_bytes = struct.pack('B'*len(sender), *sender)
    logger.info('s_CRC: {scrc:04X} s_wordlength: {len} clock freq: {clk:n}'.format(scrc = int(struct.unpack('H', packed_CRC)[0]), len = len(sender), clk = SPICLOCKFREQ_HZ))
    
    if __debug__:  
        logger.debug('s_bytes: '+''.join(r'{b:02x} '.format(b = byte) for byte in sent_bytes))

    resp = []
    receiver = []

    for i in range(0, len(sender), 2):
        ### 
        # IOT2000 : necessary to set and reset the CS-Pin by hand
        if (platform.machine() == "i586"):
            set_chipselect(0)
        ###

        res2 = spi.xfer( [sender[i+1], sender[i]], SPICLOCKFREQ_HZ) #20000) # clock freq
        
        ###
        # IOT2000 : manually drive CS back
        if (platform.machine() == "i586"):
            set_chipselect(1) 
        ###

        resp.append(res2[1])
        resp.append(res2[0])

    resp_bytes = struct.pack('B'*len(resp), *resp)
    
    if __debug__:
        logger.debug('r_bytes: '+''.join(r'{b:02x} '.format(b = byte) for byte in resp_bytes))
    resp_calcCrc = struct.unpack('H'*((len(resp_bytes)//2)), resp_bytes)
    
    # now, retr the Checksum from the response package
    recv_CRC = struct.unpack_from('H', resp_bytes, -2)[0]
 

    for byte in resp_calcCrc:
        receiver.append(byte)

    calc_CRC = CalcCrc(receiver, (len(receiver)-1))

    if(recv_CRC == calc_CRC):
        r_CRC_ok = 1
    else:
        r_CRC_ok = 0

    logger.info('r_wordlength: {len} r_CRC: {rcrc:04X} calc_r_CRC: {crcrc:04X} r_CRC_ok: {rcrcok}'.format(len = len(resp), rcrc = recv_CRC, crcrc = calc_CRC, rcrcok = r_CRC_ok))

    return resp_bytes, r_CRC_ok

