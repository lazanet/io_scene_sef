#!/bin/python3

#from io_scene_sef.sef_definitions import *

filein = '/home/lazanet/training/training.sef'
#with open(filein, 'r') as file:
#    world = SEFWorld.load_data(file)
fileout = '/home/lazanet/training/test.sef'
#with open(fileout, 'w') as file:
#    world.store_data(file)

from io_scene_sef.import_actions import *
from io_scene_sef.export_actions import *
load_sef(filein)
save_sef(fileout)
load_sef(fileout)
