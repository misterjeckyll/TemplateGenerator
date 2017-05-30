#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Inkscape Extension to draw lasercut ready Box paths from selection and options
'''

import sys
sys.path.append('/usr/share/inkscape/extensions')

# We will use the inkex module with the predefined Effect base class.
import inkex,simplepath
# The simplestyle module provides functions for style parsing.
from simplestyle import *
from fablab_lib import BaseEffect
from fablab_box_lib import BoxEffect

#----------------------------------------------------------------#
# Utility functions
#----------------------------------------------------------------#

def print_(*arg):
    f = open("fablab_debug.log", "a")
    for s in arg:
        s = str(unicode(s).encode('unicode_escape')) + " "
        f.write(s)
    f.write("\n")
    f.close()

#----------------------------------------------------------------#
# Box generator class
#----------------------------------------------------------------#
class BoxSelectionGeneratorEffect(BaseEffect, BoxEffect):

    def __init__(self):
        """
        Constructor.
        Defines the "--what" option of a script.
        """
        # Call the base class constructor.
        BaseEffect.__init__(self)

        ### The list of shapes to draw
        self.list_of_paths = []

        ### Parameters
        self.OptionParser.add_option('-i', '--path_id', action='store',type='string',   dest='path_id',     default='box',  help='Id of svg path')
        self.OptionParser.add_option('--height',        action='store',type='float',    dest='height',      default=50,     help='Hauteur de la boite')
        self.OptionParser.add_option('--thickness',     action='store',type='float',    dest='thickness',   default=3,      help='Epaisseur du materiau')
        self.OptionParser.add_option('--backlash',      action='store',type='float',    dest='backlash',    default=0.1,    help='Matière enlevé par le laser')
        self.OptionParser.add_option('--type',          action="store",type='string',   dest='type',        default='e',    help='type de boite')
        self.OptionParser.add_option('--tab_size',      action='store',type='float',    dest='tab_size',    default=10,     help='Tab size')
        self.OptionParser.add_option('--layeroffset',      action='store',type='float',    dest='layeroffset',    default=0,     help='espace libre au dessus des compartiements')
        self.OptionParser.add_option("", "--active-tab",action="store",type="string",   dest="active_tab",  default='title',help="Active tab.")

#------------------------------------------------------------------#
# Main function called when the extension is run.
#------------------------------------------------------------------#
    def effect(self):

        ### Get width, depth and intern layer position from selection
        width, depth = 0,0
        segment_pos = {'V':[],'H':[]}
        for id,node in self.selected.iteritems():
            if node.tag == inkex.addNS('rect','svg'):
                # Get selected rectangle info
                x_pos = float(node.get('x'))
                y_pos  = float(node.get('y'))
                depth = float(node.get('height'))
                width = float(node.get('width'))
            elif node.tag == inkex.addNS('path','svg'):
                # Put the selected segment position in a dictionnary
                pathrepr = node.get('d').replace(',',' ').split()
                segment_pos['V'].append(float(pathrepr[1])) if ('V'or'v') in pathrepr else None
                segment_pos['H'].append(float(pathrepr[2])) if ('H' or 'h') in pathrepr else None

        if(width==0 or depth == 0):# exit if no rectangle selected
            inkex.debug("Aucun rectangle n'a été sélectionné")
            exit()

        ### Gather incoming params
        centre = self.view_center
        layeroffset = self.options.layeroffset
        height = self.options.height
        backlash = self.options.backlash
        thickness = self.options.thickness
        tab_size = self.options.tab_size
        free = 3.

        self.prefix = self.options.path_id
        self.fg = "#FF0000"
        self.bg = None
        self.boxparams = (width, depth,height, tab_size,thickness ,backlash)

        ### Create a dictionary of the offset to the rectangle of each selected segments
        segment_offset = {'V':[],'H':[]}
        [[segment_offset[key].append(position-y_pos)if key=='H' else segment_offset[key].append(position-x_pos)] for key,elt_list in segment_pos.iteritems() for position in elt_list ]

        ### Layout of the different parts of the box
        self.layout = {
            'bottom' : [0,0],
            'top' : [free + width,0],
            'front' : [0,depth+free],
            'back' : [width+free,depth + free],
            'left' : [2*free,depth + height+2*free],
            'right' : [depth+3*free,depth + height+2*free],
            'Hlayer' : [2*free,depth + 2*height+3*free],
            'Vlayer' : [4*free+width,depth + 2*height+3*free]
        }
        ### Decide wich type of box to generate
        arglist = [centre[0], centre[1],segment_offset,layeroffset]
        type =self.options.type
        if type=='f':
            self.box_with_top_selection(*arglist)
        elif type=='o':
            self.box_without_top_selection(*arglist,lid = False),
        elif type=='oc':
            self.box_without_top_selection(*arglist,lid = True),
        elif type=='oe':
            self.box_without_top_stackable_selection(*arglist,lid = False)

        ### Create a group for each parts of the box
        parent = {}
        [parent.setdefault(group_name,inkex.etree.SubElement(self.current_layer, 'g', {inkex.addNS('label', 'inkscape'): self.options.path_id+"_"+group_name})) for group_name in ['bottom','top','front','back','left','right','Horizontal','Vertical']]
        ### Add every shapes in the correct group based on its id
        for shape in self.list_of_paths:
            id_split=shape.get('id').split('_')
            inkex.etree.SubElement(parent[id_split[1]], inkex.addNS('path', 'svg'), shape)

if __name__ == '__main__':
    effect = BoxSelectionGeneratorEffect()
    effect.affect()