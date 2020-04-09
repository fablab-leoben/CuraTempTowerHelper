# -*- coding: utf-8 -*-
# 2019, Roland Schmidt
import json

from ..Script import Script

from UM.Application import Application #To get the current printer's settings.
from UM.Logger import Logger

from typing import List, Tuple

class TempTowerHelper(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        # Create settings as an object
        settings = {
            'name': 'Temp Tower Helper',
            'key': 'TempTowerHelper',
            'metadata': {},
            'version': 2,
            'settings': {
                'start_temperature': {
                    'label': 'Start Temperature',
                    'description': 'Initial nozzle temperature',
                    'unit': '°C',
                    'type': 'int',
                    'default_value': 230
                },
                'height_increment': {
                    'label': 'Height increment without base',
                    'description': (
                        'Adjust temperature each time height param '
                        'changes by this much'
                    ),
                    'unit': 'mm',
                    'type': 'int',
                    'default_value': 10
                },
                'temperature_increment': {
                    'label': 'Temperature Increment',
                    'description': (
                        'Decrease temperature by this much with each '
                        'height increment'
                    ),
                    'unit': '°C',
                    'type': 'int',
                    'default_value': 5
                },
                'base_height': {
                    'label': 'Base height',
                    'description': (
                        'Insert here the height of the base if present '
                        'base height'
                    ),
                    'unit': 'mm',
                    'type': 'float',
                    'default_value': 1.3
                }
            }
        }

        # Dump to json string
        json_settings = json.dumps(settings)
        return json_settings


    def execute(self, data: List[str]) -> List[str]:
        # Grab settings variables
        start_temp = self.getSettingValueByKey('start_temperature')
        height_inc = self.getSettingValueByKey('height_increment')
        temp_inc = self.getSettingValueByKey('temperature_increment')
        base_height = self.getSettingValueByKey('base_height')
        # print_temperature_0 = Application.getInstance().getGlobalContainerStack().getProperty("print_temperature_0", "value")
        print_temperature = Application.getInstance().getGlobalContainerStack().getProperty("material_print_temperature_0", "value")

        # Set initial state
        output = []  
        layers_started = False
        new_temp = 0
        next_temp_change_at_height = 0
        nrTempChange = 0
        current_height = 0
        
        for layer in data:
            output_line = ''
            for line in layer.split('\n'):
                
                # pass all lines to output since none of them is edited
                output_line += '{}\n'.format(line)
                
                if ";LAYER:0" in line:
                    output_line += ';TYPE:CUSTOM\n'
                    output_line += ';print_temperature is {}\n'.format(print_temperature)
                    layers_started = True
                    next_temp_change_at_height = height_inc + base_height # compute height of first (next) temp change
                    output_line += ';{}\n'.format(next_temp_change_at_height)
                
                if line.startswith(';') or not layers_started:
                    continue

                # If a Z instruction is in the line, read the current Z
                if self.getValue(line, "Z") is not None:
                    current_height = self.getValue(line, "Z")
                    output_line += ';TYPE:CUSTOM\n'
                    output_line += ';current height is {}\n'.format(current_height)
                    output_line += ';next temp change at {} mm\n'.format(next_temp_change_at_height)
                    if current_height >= next_temp_change_at_height:
                        nrTempChange += 1
                        new_temp = start_temp + nrTempChange*temp_inc
                        output_line += ';TYPE:CUSTOM\n'
                        output_line += ';Temp Change #{}\n'.format(nrTempChange)
                        output_line += 'M104 S{}\n'.format(new_temp)
                        next_temp_change_at_height = height_inc*(nrTempChange+1) + base_height

            output.append(output_line)
        return output