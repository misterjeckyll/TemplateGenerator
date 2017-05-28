#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Inkscape Extension to generate an svg box pattern to be cut with a laser cutter
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

        ### The list of shapes to be drawed
        self.list_of_paths = []

        self.OptionParser.add_option('-i', '--path_id', action='store',type='string',   dest='path_id',     default='box',  help='Id of svg path')
        self.OptionParser.add_option('--height',        action='store',type='float',    dest='height',      default=50,     help='Hauteur de la boite')
        self.OptionParser.add_option('--thickness',     action='store',type='float',    dest='thickness',   default=3,      help='Epaisseur du materiau')
        self.OptionParser.add_option('--backlash',      action='store',type='float',    dest='backlash',    default=0.1,    help='Matière enlevé par le laser')
        self.OptionParser.add_option('--type',          action="store",type='string',   dest='type',        default='e',    help='type de boite')
        self.OptionParser.add_option('--tab_size',      action='store',type='float',    dest='tab_size',    default=10,     help='Tab size')
        self.OptionParser.add_option('--layeroffset',      action='store',type='float',    dest='layeroffset',    default=0,     help='espace libre au dessus des compartiements')
        self.OptionParser.add_option("", "--active-tab",action="store",type="string",   dest="active_tab",  default='title',help="Active tab.")
        self.start_stop = {}

#------------------------------------------------------------------#
# Main function called when the extension is run.
#------------------------------------------------------------------#
    def effect(self):
        """ Generate lasercut ready Boxe paths from selection and options
        """
        ### Global params
        parent = self.current_layer
        centre = self.view_center
        fgcolor = "#FF0000"
        bgcolor = None
        width, depth = 0,0
        height = self.options.height
        layeroffset = self.options.layeroffset
        thickness = self.options.thickness
        document_height = self.unittouu(self.document.getroot().get('height'))

        ### Gather incoming params from selection
        segment_pos = {'V':[],'H':[]}
        for id,node in self.selected.iteritems():
            if node.tag == inkex.addNS('rect','svg'):
                # Get selected rectangle info
                x_pos = float(node.get('x'))
                y_pos  = float(node.get('y'))
                depth = float(node.get('height'))
                width = float(node.get('width'))
            elif node.tag == inkex.addNS('path','svg'):
                # Gather the selected segment position in a dictionnary
                pathrepr = node.get('d').replace(',',' ').split()
                segment_pos['V'].append(float(pathrepr[1])) if ('V'or'v') in pathrepr else None
                segment_pos['H'].append(float(pathrepr[2])) if ('H' or 'h') in pathrepr else None

        if(width==0 or depth == 0):# exit if no rectangle selected
            inkex.debug("Aucun rectangle trouvé dans la selection")
            exit()

        ### Build a dictionary of the offset of each segment selected
        segment_offset = {'V':[],'H':[]}
        [[segment_offset[key].append(position-y_pos)if key=='H' else segment_offset[key].append(position-x_pos)] for key,elt_list in segment_pos.iteritems() for position in elt_list ]
        #inkex.debug(segment_offset)

        ### Pieces layout
        layout = {
            'bottom_pos' : [0,0],
            'top_pos' : [thickness + width,0],
            'front_pos' : [0,depth+thickness],
            'back_pos' : [width+thickness,depth + thickness],
            'left_pos' : [2*thickness,depth + height+2*thickness],
            'right_pos' : [depth+3*thickness,depth + height+2*thickness],
            'H_layer_pos' : [2*thickness,depth + 2*height+3*thickness],
            'V_layer_pos' : [4*thickness+width,depth + 2*height+3*thickness]
        }
        
        ### Decide wich type of box to generate
        arg =self.options.type
        if arg=='f':
            self._box_with_top_selection(layout,self.options.path_id, centre[0], centre[1], bgcolor, fgcolor, width, depth, height, self.options.tab_size, self.options.thickness, self.options.backlash,segment_offset,layeroffset)
        elif arg=='o':
            self._box_without_top_selection(layout,self.options.path_id, centre[0], centre[1], bgcolor, fgcolor, width, depth, height, self.options.tab_size, self.options.thickness, self.options.backlash,segment_offset,layeroffset,False),
        elif arg=='oc':
            self._box_without_top_selection(layout,self.options.path_id, centre[0], centre[1], bgcolor, fgcolor, width, depth, height, self.options.tab_size, self.options.thickness, self.options.backlash,segment_offset,layeroffset,True),
        elif arg=='oe':
            self._box_without_top_stackable_selection(layout,self.options.path_id, centre[0], centre[1], bgcolor, fgcolor, width, depth, height, self.options.tab_size, self.options.thickness, self.options.backlash,segment_offset,layeroffset,False)

        parent = {}
        [parent.setdefault(group_name,inkex.etree.SubElement(self.current_layer, 'g', {inkex.addNS('label', 'inkscape'): self.options.path_id+"_"+group_name})) for group_name in ['bottom','top','front','back','left','right','Horizontal','Vertical']]

        for shape in self.list_of_paths:
            id_split=shape.get('id').split('_')
            inkex.etree.SubElement(parent[id_split[1]], inkex.addNS('path', 'svg'), shape)

if __name__ == '__main__':
    effect = BoxSelectionGeneratorEffect()
    effect.affect()