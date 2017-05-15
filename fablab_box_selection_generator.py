import sys
sys.path.append('/usr/share/inkscape/extensions')

# We will use the inkex module with the predefined Effect base class.
import inkex
# The simplestyle module provides functions for style parsing.
from simplestyle import *
import simplepath

from fablab_lib import BaseEffect
from fablab_box_lib import BoxEffect

#----------------------------------------------------------------#
### Utility functions
#----------------------------------------------------------------#

def print_(*arg):
    f = open("fablab_debug.log", "a")
    for s in arg:
        s = str(unicode(s).encode('unicode_escape')) + " "
        f.write(s)
    f.write("\n")
    f.close()

#----------------------------------------------------------------#
### Box generator class
#----------------------------------------------------------------#
class BoxSelectionGeneratorEffect(BaseEffect, BoxEffect):

    def __init__(self):
        """
        Constructor.
        Defines the "--what" option of a script.
        """
        # Call the base class constructor.
        BaseEffect.__init__(self)

        self.OptionParser.add_option('-i', '--path_id', action='store',
                                     type='string', dest='path_id', default='box',
                                     help='Id of svg path')

        self.OptionParser.add_option('--height', action='store',
                                     type='float', dest='height', default=50,
                                     help='Hauteur de la boite')
        self.OptionParser.add_option('--thickness', action='store',
                                     type='float', dest='thickness', default=3,
                                     help='Epaisseur du materiau')

        self.OptionParser.add_option('--backlash', action='store',
                                     type='float', dest='backlash', default=0.1,
                                     help='Matiere enleve par le laser')
        self.OptionParser.add_option('--top', action="store",
                                     type='string', dest='top', help='top edge', default='e')

        self.start_stop = {}

# ----------------------------------------------------------------------#
### Main function called when the extension is run.
# ----------------------------------------------------------------------#
    def effect(self):
        """ Calculate Box cutting path from selection and options
        """
        ### Global params - Debug

        parent = self.current_layer
        centre = self.view_center
        fgcolor = "#FF0000"
        bgcolor = None
        choices = ['e', 'c', 'E', 'S', 'i', 'k', 'v', 'f', 'L']

        inkex.debug("-- %s -- %s --" % (centre[0], centre[1]))
        inkex.debug(self.options)

        ### Gather incoming params from options and selection

        height = self.options.height

        if(True):
            for shape in self.box_with_top(self.options.path_id, centre[0], centre[1], bgcolor, fgcolor, self.options.width, self.options.depth, self.options.height, self.options.tab_size, self.options.thickness, self.options.backlash,self.options.backlash):
                inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), shape)
        else:
            for shape in self.box_without_top(self.options.path_id, centre[0], centre[1], bgcolor, fgcolor, self.options.width, self.options.depth, self.options.height, self.options.tab_size, self.options.thickness, self.options.backlash):
                inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), shape)

        #inkex.etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )


if __name__ == '__main__':
    effect = BoxSelectionGeneratorEffect()
    effect.affect()