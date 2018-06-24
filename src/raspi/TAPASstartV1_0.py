#!/usr/bin/env python3
###################################################################################################
## SDI TAPAS python demo application - main module
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

# import for platform check
import platform

# modules for spi communication
import spidev
import TAPASComm

# other modules for data handling
import struct
import json

# modules for implementing user interface
import curses
import time

import pprint
import logging
import threading

# global constants
RATED_CURRENT_RUN = 2.5
SERVO_MOTOR = "1"
MODEL_MOTOR = "2"

logging.basicConfig( level=logging.INFO
                   , style='{'
                   , format='{asctime} {levelname} {name} ({filename} +{lineno}) {module}::{funcName} [{process}/{thread}] {message}'
                   , datefmt='%Y-%m-%dT%H:%M:%S %z'
                   
)
logger=logging.getLogger(__name__) #'__name__')
#logger.setLevel(logging.DEBUG)
#ch = logging.StreamHandler()
#ch.setLevel(logging.ERROR)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'
def _raspispidevidx(idx=0):
    raspispidev=((0, 0), (0,1), (1,0), (1,1), (1,2))
    spidev_bus_device_tuple = raspispidev[idx]
    if __debug__:
        logger.debug('For idx={index} select (bus,device)=({tup[0]},{tup[1]})'.format(tup=spidev_bus_device_tuple, index=idx))
    return spidev_bus_device_tuple 
def _openspidev(idx=0):
    logging.info('Lookup (bus,device) for index: {index}'.format(index=idx))
    bus_device_tuple=_raspispidevidx(idx)   
    spi=spidev.SpiDev()
    spi.open(bus_device_tuple[0], bus_device_tuple[1])
    logging.info('Called spidev.open({tup[0]},{tup[1]})'.format(tup=bus_device_tuple))
    return spi
    
###
# this function is necessary for running the script on IOT2000 platform
# exporting gpio file
def export_gpio ():
    export = "/sys/class/gpio/export"
    file = open(export, 'w')
    file.write("10")
if (platform.machine() == "i586"):
    export_gpio()
### 

# defining the names for the states of Controller-state-machine, estimator and custom user errors
_CTRL_states_ = ["CTRL_State_Error","CTRL_State_Idle","CTRL_State_OffLine","CTRL_State_OnLine","CTRL_numStates","CTRL_State_unknown"]
   
_EST_states_ = ["EST_State_Error","EST_State_Idle","EST_State_RoverL","EST_State_Rs","EST_State_RampUp","EST_State_IdRated",
                "EST_State_RatedFlux_OL","EST_State_RatedFlux","EST_StateRampDown","EST_StateLockRotor","EST_State_Ls","EST_State_Rr",
                "EST_State_MotorIdentified","EST_State_OnLine","EST_numStates","EST_State_unknown"]  

_PROTECT_states_ = ["Normal_OP", "PROTECT_OVERTEMP", "PROTECT_OVERCURRENT", "PROTECT_UNKNOWN"]

# start application
# set title of terminal window
title = "SDI TAPAS BOARD QUICK START" 
print("\x1b]2;%s\x07" % title)

# initialize SPI-HW
#spi = spidev.SpiDev()

if (platform.machine() == "i586"):
    # open spi connection on IOT2040
    #spi.open(1,0) 
    spi=_openspidev(2)
else :
    # e.g. for raspberry pi zero (w) 
    #spi.open(0,0)
    spi=_openspidev(0)

spi.bits_per_word = 8 
spi.mode = 3
# init variables
callNo = 0
RoverLestFrequencyHz = 0.0
fluxEstFrequency = 0.0
motorParametersSet = 0
motorIsIdentified = 0
# init table for CRC
TAPASComm.GenerateCrcTable()	

# synchronize the communication with the slave
syncStatus = 0
SPIstatusTest = 0
countTransactionsSuccess = 0

#TAPASComm.getZeroCoCoMODict()
#TAPASComm.getZeroCoCoSODict()
#ret=TAPASComm.xferCoilCommunication(spi)
#quit()
class MessageCounter():
  def __init__(self):
      self.value = 0
      self.VALUE_CAP = 2**16-1
  def increment(self):
      if self.value < self.VALUE_CAP:
          self.value += 1
      else:
          self.reset()
  def reset(self):
      self.value = 1
try : 
    msgseqno=MessageCounter();
    while syncStatus != 1:
        msgseqno.increment()
        logger.info('### msgseqno: {:05}'.format(msgseqno.value))

        master_tx_dict=TAPASComm.getZeroCoCoMODict()
#        master_tx_dict["flags"]= Senden_flags
        master_tx_dict["u_msgseq"] = msgseqno.value
        ret = TAPASComm.xferCoilCommunication(spi, master_tx_dict)
 
        if(ret["r_CRC_ok"] == 1):
            countTransactionsSuccess += 1
            if(((ret["spiStatus"] == 0x1ABC) or (ret["spiStatus"] == 0x2ABC)) and (countTransactionsSuccess > 15)):
                syncStatus = 1
            else:    
                syncStatus = 0
        else:   
            syncStatus = 0
#define CACTUS_NOT_OK 0
#define CACTUS_NO_RECEIVE 1
#define CACTUS_NEW_DATA_OK 2

        logger.info('spi status slave: {spistatus:#04x} success cnt: {cnt} sync status: {sync}'.format(spistatus = int(ret["spiStatus"]), cnt = countTransactionsSuccess, sync = syncStatus))
except KeyboardInterrupt :

    #win.addstr(10,5, "User abort of connection procedure...", curses.A_BOLD)
    #win.refresh()
    #curses.nocbreak()
    #stdscr.keypad(0)
    #curses.echo()
    #curses.endwin()

    spi.close()
    time.sleep(1.5)

    quit()


#initialize "curses"-module for console management
#stdscr = curses.initscr()
#curses.noecho()
#curses.cbreak()

###
# this one is not executable on the iot2040
#if not (platform.machine() == "i586"):
    # e.g. raspberry pi lib supports this 
#    curses.curs_set(False)
###

#stdscr.keypad(1)
#curses.start_color()
#curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_WHITE)
#curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
#curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
#curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_WHITE)

#stdscr.bkgd(curses.color_pair(1))
#stdscr.refresh()
 
#win = curses.newwin(40, 85, 1, 2)
#win.bkgd(curses.color_pair(2))
#win.box()

#win.addstr(1,2, "Connected to slave...")
#win.refresh()

# when sync is done 
# -> start the interactive part
#quit()
try:	
    msgseqno=MessageCounter();
    coilmodeack=False;
    while True:
        # force values
        polePairs=1
        ratedCurrent=0.001
        motorType = MODEL_MOTOR
        # clear screen and print buffer
        if motorType == SERVO_MOTOR:
#                        win.addstr(17, 2, "--> Selected a servo motor                                              ")
#                        win.refresh()
                        RoverLestFrequencyHz = 150.0
                        fluxEstFrequency = 50.0
                        motorParametersSet = 1
                        motorTypeInputSucc = 1
        elif motorType == MODEL_MOTOR:
#                        win.addstr(17, 2, "--> Selected a hobbyist motor                                              ")
#                        win.refresh()
                        RoverLestFrequencyHz = 300.0
                        fluxEstFrequency = 30.0
                        motorParametersSet = 1
                        motorTypeInputSucc = 1
        
        selectedMode = "256" # 2 identify 3 run 4 disable 5 shutdown?
        if selectedMode == "256" :
            Senden_flags=0x0101 # 0x0100 "Coil Mode"
            msgseqno.increment()
#            while not coilmodeack:
#                master_tx_cmd=TAPASComm.getNeutralMasterTxDict()
#                master_tx_cmd["flags"]=Senden_flags
#                 ret=TAPASComm.commMasterSlave(spi, master_tx_cmd)
#                if ret["flags"] == 257:
#                    coilmodeack=True
 
            master_tx_dict=TAPASComm.getZeroCoCoMODict()
            master_tx_dict["flags"]= Senden_flags
            master_tx_dict["u_msgseq"] = msgseqno.value
            ret = TAPASComm.xferCoilCommunication(spi, master_tx_dict)
            
        elif selectedMode == "2" : 
            # start id
                # 
                Senden_flags = 1 
                #(enableSys)
                
                master_tx_cmd=TAPASComm.getNeutralMasterTxDict()
                master_tx_cmd["flags"]=Senden_flags
                master_tx_cmd["i_Motor_numPolePairs"]=int(polePairs)
                master_tx_cmd["f_Motor_ratedCurrent"]=float(ratedCurrent)
                master_tx_cmd["f_Motor_RoverLestFrequencyHz"]=float(RoverLestFrequencyHz)
                master_tx_cmd["f_Motor_fluxEstFrequency"]=float(fluxEstFrequency)
                master_tx_cmd["f_CTRL_setpoint_speed"]=1.0
                master_tx_cmd["f_CTRL_setpoint_accel"]=1.0

                for i in range(0,4):
                    ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)
                    logger.info('spi status slave: {spistatus:#0.4x}'.format(spistatus = int(ret["spiStatus"]), cnt = syncStatus))

                Senden_flags = 3 # set run and identify bits
                master_tx_cmd["flags"]=Senden_flags

                runConfiguration = 0
                
                try : 
                    while ((ret["flags"] & (1 << 5)) == 0):
                        ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)
                        print ("spi status slave: %#0.4x" % int(ret["spi status slave"]))

                        # monitor the CTRL_state index
                        if(ret["controller state [CTRL_state]"] > 4):
                            ret["controller state [CTRL_state]"] = 5

                        # monitor the EST_state index
                        if(ret["estimator state [EST_state]"] > 14):	
                            ret["estimator state [EST_state]"] = 15
                
                        # check the TAPAS-slave for a protection error
                        if(ret["Protection mode"] != 0):
                            Senden_flags = 0
                            motorIsIdentified = 0
                            if(ret["Protection mode"] > 2) :
                                ret["Protection mode"] = 3
#                            win.addstr(11, 5, "SDI TAPAS-Board reported an " + str(_PROTECT_states_[int(ret["Protection mode"])]) + "!", curses.color_pair(3))
#                           win.addstr(12, 5, "Restart identification to continue")
                            master_tx_cmd["flags"]=Senden_flags
                            master_tx_cmd["f_CTRL_setpoint_speed"]=0.0
                            master_tx_cmd["f_CTRL_setpoint_accel"]=0.0
                            for i in range(0,3):
                                ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)
                                time.sleep(1.5) 
                            break
                                                     
#                        win.addstr(1, 2, " SDI TAPAS BOARD QUICK START - MOTOR IDENTIFICATION ", curses.A_BOLD)
#                        win.addstr(2, 2, "###################################################")
#                        win.addstr(3, 2, "--------------current SDI TAPAS-board data-------------")
#                        win.addstr(4, 2, "* Protection mode..............: " + _PROTECT_states_[ret["Protection mode"]])
#                        win.addstr(5, 2, "* dc-bus voltage...............: " + str(round((ret["dc-bus voltage"]*1000.0),2)))
#                        win.addstr(5, 43, "   [V] ")
#                        win.addstr(6, 2, "* dc-bus current...............: " + str(round((ret["dc-bus current"]),2)))
#                        win.addstr(6, 43, "   [A] ")
#                        win.addstr(7, 2, "* dc-bus power.................: " + str(round(((ret["dc-bus voltage"]*1000.0)*ret["dc-bus current"]),2)))
#                        win.addstr(7, 43, "   [W] ")
#                        win.addstr(8, 2, "* board-temperature............: " + str(round((ret["board-temperature"]),2)))
#                        win.addstr(8, 43, "   [C] ")
#                        win.addstr(9, 2, "* motor speed..................: " + str(round((ret["motor speed"]*1000.0),2)))
#                        win.addstr(9, 43, "  [rpm] ")
#                        win.addstr(10,2, "* controller state [CTRL_state]: " + _CTRL_states_[int(ret["controller state [CTRL_state]"])])
#                        win.addstr(11,2, "* estimator state [EST_state]..: " + _EST_states_[int(ret["estimator state [EST_state]"])])
#                        win.addstr(12,2, "------------identified motor parameters------------")                 
#                        win.addstr(13,2, "* motorRs......................: " + str(round(ret["motorRs"],7)))
#                        win.addstr(13,43, "  [Ohm] ")
#                        win.addstr(14,2, "* motorRr......................: " + str(round(ret["motorRr"],7)))
#                        win.addstr(14,43, "  [Ohm] ")
#                        win.addstr(15,2, "* motorLsd.....................: " + str(round(ret["motorLsd"],7)))
#                        win.addstr(15,43, " [Henry] ")
#                        win.addstr(16,2, "* motorLsq.....................: " + str(round(ret["motorLsq"],7)))
#                        win.addstr(16,43, " [Henry] ")
#                        win.addstr(17,2, "* ratedFlux....................: " + str(round(ret["ratedFlux"],7)))
#                        win.addstr(17,43, "  [V/Hz] ")
#                        win.addstr(18,2, "---------------------------------------------------")
                        if(ret["spi connection status"] == 1) :
                             logger.info('checksum correct - data valid')
#                            win.addstr(19,6, "  checksum correct - data valid  ")
                        else :
                             logger.warn('checksum incorrect - data invalid')
#                            win.addstr(19,6, "!!checksum incorrect - data invalid!!", curses.color_pair(3))
#                        win.addstr(20,2, "###################################################")   
#                        win.addstr(22,2, "Identifying connected motor - please wait ...", curses.A_BOLD)
#                        win.addstr(24,4, "ABORT WITH CTRL-C", curses.color_pair(3))
#                        win.refresh()
                        time.sleep(0.2)

                    ratedCurrent = RATED_CURRENT_RUN    
                    Senden_flags = 1 # system remains enabled

#                    master_tx_cmd=TAPASComm.getNeutralMasterTxDict()
                    master_tx_cmd["flags"]=Senden_flags
#                    master_tx_cmd["i_Motor_numPolePairs"]=int(polePairs)
                    master_tx_cmd["f_Motor_ratedCurrent"]=float(ratedCurrent)
#                    master_tx_cmd["f_Motor_RoverLestFrequencyHz"]=float(RoverLestFrequencyHz)
#                    master_tx_cmd["f_Motor_fluxEstFrequency"]=float(fluxEstFrequency)
                    master_tx_cmd["f_CTRL_setpoint_speed"]=0.0
                    master_tx_cmd["f_CTRL_setpoint_accel"]=0.0

                    for i in range(0,3):
                       ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)
                       print ("spi status slave: %i" % int(ret["spi status slave"]))

#                    win.addstr(22, 2, "                                                 ")
#                    win.addstr(22, 2, "Motor identification successful", curses.color_pair(1))
#                    win.addstr(23, 4, "Please press <s> to save the identified motor                     ")
#                    win.addstr(24, 4, "parameters to file or any other key to quit without saving                ")
#                    win.refresh()
                
                    # save or not save ? 
#                    sel = chr(stdscr.getch(28,4))
                    motorIsIdentified = 1
                    sel='s'
                    if(sel == 's'):
                        json.dump(ret, open("yourMotorParams.json","w") )
                except KeyboardInterrupt:
                    Senden_flags = 0
                    motorParametersSet = 0
                    motorIsIdentified = 0
                    ratedCurrent = 0.0
                    master_tx_cmd=TAPASComm.getNeutralMasterTxDict()
                    master_tx_cmd["flags"]=Senden_flags
                    master_tx_cmd["i_Motor_numPolePairs"]=int(polePairs)
                    master_tx_cmd["f_Motor_ratedCurrent"]=float(ratedCurrent)
                    master_tx_cmd["f_Motor_RoverLestFrequencyHz"]=float(RoverLestFrequencyHz)
                    master_tx_cmd["f_Motor_fluxEstFrequency"]=float(fluxEstFrequency)
#                    master_tx_cmd["f_CTRL_setpoint_speed"]=0.0
#                    master_tx_cmd["f_CTRL_setpoint_accel"]=0.0

                    for i in range(0,3):
                       ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)

#                    win.addstr(11, 5, "User canceled motor identification, disabling inverter", curses.color_pair(3))
#                    win.addstr(12, 5, "Enter motor parameters again - see (1)", curses.color_pair(3))
                    time.sleep(1.5)                
        elif selectedMode == "3" :
            if(motorIsIdentified != 1):
#                win.addstr(11,5, "Identify motor first - see (2)! ", curses.color_pair(3))
                time.sleep(1.5)
            else:

                Senden_flags = 3
        # get setpoint for the maximum acceleration
#                win.addstr(1,2,"SDI TAPAS BOARD QUICK START - RUN MOTOR", curses.A_BOLD)
#                win.addstr(2, 2, "###################################################")
#                win.addstr(3,2,"a) Set maximum acceleration in [rpm/s]")
#                win.addstr(4,4,"100.0", curses.color_pair(4)) 
#                win.refresh()
        
                getMaxAccSucc = 0
                while(getMaxAccSucc == 0): 
                    try:
                        setMaxAcc = float(setMaxAcc)
                        if(setMaxAcc > 1500.0):
                                setMaxAcc = 1500
#                                win.addstr(5,6, "HINT: Acceleration limited to 1500 rpm/s for security reasons", curses.A_BOLD)
                        setMaxAcc /= 1000.0
                        getMaxAccSucc = 1
                    except ValueError:
                        time.sleep(1.5)
                        getMaxAccSucc = 0
                
         # get setpoint for the motor speed
#                win.addstr(7,2,"b) Set speed [rpm] ")
#                win.addstr(8,4,"200", curses.color_pair(4))
                
                getSpeedSucc = 0
                while(getSpeedSucc == 0): 
                    try: 
                        setSpeed = stdscr.getstr(9, 6)
                        setSpeed = float(setSpeed)
                        setSpeed /= 1000.0
                        getSpeedSucc = 1
                    except ValueError:
                        time.sleep(1.5) 
                        getSpeedSucc = 0


#                win.addstr(10 ,6," -> Your acceleration : " + str(setMaxAcc*1000.0) + " [rpm/s]")
#                win.addstr(11 ,6," -> Your motor speed  : " + str(setSpeed*1000.0) + " [rpm]")
#                win.addstr(12 ,6," -> To stop observing values, hit Ctrl-C")
                time.sleep(1.0)

                readData = 1
                ratedCurrent = RATED_CURRENT_RUN
                master_tx_cmd=TAPASComm.getNeutralMasterTxDict()
                master_tx_cmd["flags"]=Senden_flags
                master_tx_cmd["i_Motor_numPolePairs"]=int(polePairs)
                master_tx_cmd["f_Motor_ratedCurrent"]=float(ratedCurrent)
                master_tx_cmd["f_Motor_RoverLestFrequencyHz"]=float(RoverLestFrequencyHz)
                master_tx_cmd["f_Motor_fluxEstFrequency"]=float(fluxEstFrequency)
                master_tx_cmd["f_CTRL_setpoint_speed"]=float(setSpeed)
                master_tx_cmd["f_CTRL_setpoint_accel"]=float(setMaxAcc)

                try : 
                    while readData:
                        ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)

                        # monitor the CTRL_state index
                        if(ret["controller state [CTRL_state]"] > 4):
                            ret["controller state [CTRL_state]"] = 5
                      
                        # monitor the EST_state index
                        if(ret["estimator state [EST_state]"] > 14):
                            ret["estimator state [EST_state]"] = 15
                      
                        # check the TAPAS-slave for a protection error
                        if(ret["Protection mode"] != 0):
                            if(ret["Protection mode"] > 2) :
                                ret["Protection mode"] = 3
                            Senden_flags = 0
                            motorIsIdentified = 0
#                            win.addstr(10, 10, "ERROR!", curses.color_pair(3))
#                            win.addstr(11, 5, "Your SDI TAPAS-Board reported an " + str(_PROTECT_states_[int(ret["Protection mode"])]) + "!", curses.color_pair(3))
                            master_tx_cmd["flags"]=Senden_flags
#                            master_tx_cmd["i_Motor_numPolePairs"]=int(polePairs)
#                            master_tx_cmd["f_Motor_ratedCurrent"]=float(ratedCurrent)
#                            master_tx_cmd["f_Motor_RoverLestFrequencyHz"]=float(RoverLestFrequencyHz)
#                            master_tx_cmd["f_Motor_fluxEstFrequency"]=float(fluxEstFrequency)
                            master_tx_cmd["f_CTRL_setpoint_speed"]=0.0
                            master_tx_cmd["f_CTRL_setpoint_accel"]=0.0
                            for i in range(0,3):
                                ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)
                      
                            readData = 0 
                            time.sleep(1.5)
                            break
                            
#                        win.erase()
#                        win.box()
#                        win.addstr(1, 2, "SDI TAPAS BOARD QICK START - OBSERVER VIEW", curses.A_BOLD)
#                        win.addstr(2, 2, "###################################################")
#                        win.addstr(3, 2, "--------------current SDI TAPAS-board data-------------")
#                        win.addstr(4, 2, "* Protection mode..............: " + _PROTECT_states_[ret["Protection mode"]])
#                        win.addstr(5, 2, "* dc-bus voltage...............: " + str(round((ret["dc-bus voltage"]*1000.0),2)))
#                        win.addstr(5, 43, "   [V] ")
#                        win.addstr(6, 2, "* dc-bus current...............: " + str(round((ret["dc-bus current"]),2)))
#                        win.addstr(6, 43, "   [A] ")
#                        win.addstr(7, 2, "* dc-bus power.................: " + str(round(((ret["dc-bus voltage"]*1000.0)*ret["dc-bus current"]),2)))
#                        win.addstr(7, 43, "   [W] ")
#                        win.addstr(8, 2, "* board-temperature............: " + str(round((ret["board-temperature"]),2)))
#                        win.addstr(8, 43, "   [C] ")
#                        win.addstr(9, 2, "* motor speed..................: " + str(round((ret["motor speed"]*1000.0),2)))
#                        win.addstr(9, 43, "  [rpm] ")
#                        win.addstr(10,2, "* controller state [CTRL_state]: " + _CTRL_states_[int(ret["controller state [CTRL_state]"])])
#                        win.addstr(11,2, "* estimator state [EST_state]..: " + _EST_states_[int(ret["estimator state [EST_state]"])])
#                        win.addstr(12,2, "---------------------------------------------------")
                        if(ret["spi connection status"] == 1) :
                            print ("  checksum correct - data valid  ")
#                            win.addstr(19,6, "  checksum correct - data valid  ")
                        else : 
                            print ("  checksum incorrect - data invalid  ")
#                            win.addstr(19,6, "!!checksum incorrect - data invalid!!", curses.color_pair(3))
#                        win.addstr(14,2, "###################################################")
#                        win.addstr(16,2, "Running motor in closed loop mode now ...", curses.A_BOLD)
#                        win.addstr(18,4, "press CTRL-C to quit this view", curses.color_pair(1))
#                        win.refresh()
                        time.sleep(0.2)
                except KeyboardInterrupt: 
                        readData = 0                   
        
        elif selectedMode == "4" : 
#            win.erase()
#            win.box()
#            win.refresh()
#            win.addstr(5,5, "Inverter now gets shut down", curses.A_BOLD)
#            win.refresh()
            motorParametersSet = 0
            motorIsIdentified = 0 

            master_tx_cmd=TAPASComm.getNeutralMasterTxDict()
            master_tx_cmd["f_Motor_RoverLestFrequencyHz"]=float(RoverLestFrequencyHz)
            master_tx_cmd["f_Motor_fluxEstFrequency"]=float(fluxEstFrequency)
            for i in range(0,3):
                ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)
            time.sleep(1.5)
        elif selectedMode == "5" :
#            win.erase()
#            win.box()
#            win.refresh()
#            win.addstr(5,5, "Disabling inverter ...", curses.A_BOLD)
#            win.addstr(6,5, "Shutting down ...", curses.A_BOLD)
#            win.refresh()
            motorParametersSet = 0
            motorIsIdentified = 0     

            master_tx_cmd=TAPASComm.getNeutralMasterTxDict()
            master_tx_cmd["f_Motor_RoverLestFrequencyHz"]=float(RoverLestFrequencyHz)
            master_tx_cmd["f_Motor_fluxEstFrequency"]=float(fluxEstFrequency)
            for i in range(0,3):
                ret = TAPASComm.commMasterSlave(spi, master_tx_cmd)
            
#            curses.nocbreak()
#            stdscr.keypad(0)
#            curses.echo()
#            curses.endwin()
             
            spi.close()

            quit()
            time.sleep(1.5)
        else :
#            win.erase()
#            win.refresh()
#            win.box()
#            win.addstr(11, 5,"Invalid selection", curses.color_pair(3))
#            win.refresh()
            time.sleep(1.5)
	
except KeyboardInterrupt:# Ctrl+C pressed, so...
#    curses.nocbreak()
#    stdscr.keypad(0)
#    curses.echo()
#    curses.endwin()

    spi.close()
#end try
