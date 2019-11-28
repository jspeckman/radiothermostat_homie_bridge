#!/usr/bin/python3

import yaml
import time

import radiotherm

from homie.device_base import Device_Base
from homie.node.node_base import Node_Base

from homie.node.property.property_setpoint import Property_Setpoint
from homie.node.property.property_temperature import Property_Temperature
from homie.node.property.property_enum import Property_Enum
from homie.node.property.property_string import Property_String

FAN_MODES = ['Auto', 'Auto/Circulate', 'On']
SYSTEM_MODES = ['Off', 'Heat', 'Cool','Auto']
HOLD_MODES = ['Disabled', 'Enabled']
UNITS = 'F'
SETPOINT_LIMITS = '55:85'


class Device_Radio_Thermostat(Device_Base):
  def __init__(self, device_id=None, name=None, homie_settings=None, mqtt_settings=None, tstat_device=None):
    super().__init__ (device_id, name, homie_settings, mqtt_settings)

    self.tstat_device=tstat_device

    node = (Node_Base(self,'controls','Controls','controls'))
    self.add_node (node)
    
    self.heat_setpoint = Property_Setpoint (node,id='heatsetpoint',name='Heat Setpoint',data_format=SETPOINT_LIMITS,unit=UNITS,value=tstat_device.t_heat['raw'],set_value = lambda value: self.set_heat_setpoint(value) )
    node.add_property (self.heat_setpoint)
    
    self.cool_setpoint = Property_Setpoint (node,id='coolsetpoint',name='Cool Setpoint',data_format=SETPOINT_LIMITS,unit=UNITS,value=tstat_device.t_cool['raw'],set_value=lambda value: self.set_cool_setpoint(value) )
    node.add_property (self.cool_setpoint)

    self.system_mode = Property_Enum (node,id='systemmode',name='System Mode',data_format=','.join(SYSTEM_MODES),value=tstat_device.tmode['human'],set_value = lambda value: self.set_system_mode(value) )
    node.add_property (self.system_mode)

    self.fan_mode = Property_Enum (node,id='fanmode',name='Fan Mode',data_format=','.join(FAN_MODES),value=tstat_device.fmode['human'],set_value = lambda value: self.set_fan_mode(value) )
    node.add_property (self.fan_mode)

    self.hold = Property_Enum (node,id='hold',name='Hold',data_format=','.join(HOLD_MODES),value=tstat_device.hold['human'],set_value = lambda value: self.set_hold(value) )
    node.add_property (self.hold)

    self.override = Property_Enum (node,id='override',name='Override',data_format=','.join(HOLD_MODES),value=tstat_device.override['human'],set_value = lambda value: self.set_override(value) )
    node.add_property (self.override)

    
    node = (Node_Base(self,'status','Status','status'))
    self.add_node (node)

    self.temperature = Property_Temperature (node,unit='F',value=tstat_device.temp['raw'])
    node.add_property (self.temperature)

    self.system_status = Property_String (node,id='systemstatus',name='System Status',value=tstat_device.tstate['human'])
    node.add_property (self.system_status)

    self.fan_status = Property_String (node,id='fanstatus',name='Fan Status',value=tstat_device.fstate['human'])
    node.add_property (self.fan_status)

    
    node = (Node_Base(self,'runtime','Runtime','runtime'))
    self.add_node (node)

    self.today_heat = Property_String (node,id='todayheat',name='Today Heat')
    node.add_property (self.today_heat)

    self.today_cool = Property_String (node,id='todaycool',name='Today Cool')
    node.add_property (self.today_cool)

    self.yesterday_heat = Property_String (node,id='yesterdayheat',name='Yesterday Heat')
    node.add_property (self.yesterday_heat)

    self.yesterday_cool = Property_String (node,id='yesterdaycool',name='Yesterday Cool')
    node.add_property (self.yesterday_cool)


    self.start()


  def get_key(self, val, human_dict): 
    for key, value in human_dict.items(): 
      if val == value: 
        return key 
    return val

  def update(self):
    self.temperature.value = self.tstat_device.temp['raw']
    self.hold.value = self.tstat_device.hold['human']
    self.override.value = self.tstat_device.override['human']
    self.fan_mode.value = self.tstat_device.fmode['human']
    self.fan_status.value = self.tstat_device.fstate['human']
    self.system_mode.value = self.tstat_device.tmode['human']
    self.heat_setpoint.value = self.tstat_device.t_heat['raw']
    self.cool_setpoint.value = self.tstat_device.t_cool['raw']
    self.system_status.value = self.tstat_device.tstate['human']

    datalog_raw = self.tstat_device.datalog['raw']
    self.today_heat.value = '%s hrs, %s min' % (datalog_raw['today']['heat_runtime']['hour'], datalog_raw['today']['heat_runtime']['minute'])
    self.today_cool.value = '%s hrs, %s min' % (datalog_raw['today']['cool_runtime']['hour'], datalog_raw['today']['cool_runtime']['minute'])
    self.yesterday_heat.value = '%s hrs, %s min' % (datalog_raw['yesterday']['heat_runtime']['hour'], datalog_raw['yesterday']['heat_runtime']['minute'])
    self.yesterday_cool.value = '%s hrs, %s min' % (datalog_raw['yesterday']['cool_runtime']['hour'], datalog_raw['yesterday']['cool_runtime']['minute'])

  def set_heat_setpoint(self,value):
    self.tstat_device.t_heat = value
    self.heat_setpoint.value = value
        
  def set_cool_setpoint(self,value):
    self.tstat_device.t_cool = value
    self.cool_setpoint.value = value
        
  def set_system_mode(self,value):
    self.tstat_device.tmode = self.get_key(value, {0 : 'Off',1 : 'Heat',2 : 'Cool',3 : 'Auto'})
    self.system_mode.value = value
        
  def set_fan_mode(self,value):
    self.tstat_device.fmode = self.get_key(value, {0 : 'Auto',1 : 'Auto/Circulate',2 : 'On'})
    self.fan_mode = value
        
  def set_hold(self,value):
    self.tstat_device.hold = self.get_key(value, {0 : 'Disabled',1 : 'Enabled'})
    self.hold.value = value


def get_config():
  try:
    with open('/etc/radio_thermostat/config.yaml', 'r') as f:
    # use safe_load instead load
      configMap = yaml.safe_load(f)
  except FileNotFoundError:
    with open('config.yaml', 'r') as f:
      configMap = yaml.safe_load(f)
  return(configMap)

configMap = get_config()

rtherm = radiotherm.get_thermostat()
name = rtherm.name['raw']

thermostat = Device_Radio_Thermostat(device_id=name.lower().replace(" ", ""), name=name, mqtt_settings=configMap['mqtt'], tstat_device=rtherm)

def main():
  last_report_time = 0

  while True:
    if (time.time() - last_report_time) > configMap['update']['interval'] * 60:
      thermostat.update()
      last_report_time = time.time()
    time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
