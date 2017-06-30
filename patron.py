#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inkscape Extension to generate a t-shirt svg template to be printed with a plotter-tracer
or a printer.
"""

import inkex
import pturtle
import simplestyle
import xml.etree.ElementTree as etree
__version__ = '0.1'

inkex.localize()


# ----------------------------------------------------------------#
#                       UTILITY FUNCTIONS
# ----------------------------------------------------------------#
# SVG element generation routine
def draw_svg_square(w, h, x, y, parent):
    style = {'stroke': 'none',
             'stroke-width': '1',
             'fill': '#000000'
             }

    attribs = {
        'style': simplestyle.formatStyle(style),
        'height': str(h),
        'width': str(w),
        'x': str(x),
        'y': str(y)
    }
    inkex.etree.SubElement(parent, inkex.addNS('rect', 'svg'), attribs)


def points_to_svgd(p, close=True):
    """ 
        convert list of points (x,y) pairs
        into a closed SVG path list
    """
    f = p[0]
    p = p[1:]
    svgd = 'M%.4f,%.4f' % (f, f)
    for x in p:
        svgd += 'L%.4f,%.4f' % x
    if close:
        svgd += 'z'
    return svgd


def points_to_bbox(p):
    """ 
        from a list of points (x,y pairs)
        - return the lower-left xy and upper-right xy
    """
    llx = urx = p[0][0]
    lly = ury = p[0][1]
    for x in p[1:]:
        if x[0] < llx:
            llx = x[0]
        elif x[0] > urx:
            urx = x[0]
        if x[1] < lly:
            lly = x[1]
        elif x[1] > ury:
            ury = x[1]
    return llx, lly, urx, ury


def points_to_bbox_center(p):
    """ 
        from a list of points (x,y pairs)
        - find midpoint of bounding box around all points
        - return (x,y)
    """
    bbox = points_to_bbox(p)
    return (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0


# ----------------------------------------------------------------#
#                   T-SHIRT TEMPLATE GENERATOR
# ----------------------------------------------------------------#
class Patron(inkex.Effect):
    """
        Patron generate the paths of a basic T-shirt template from user measurements.
        Printed, this Svg template is used as a support for sewing a t-shirt 
        with the perfect morphology.
    """

    def __init__(self):
        """
            Define how the options are mapped from the inx file
            and initialize class attributes
        """
        inkex.Effect.__init__(self)

        self.doc_center = None
        self.offset_style = {
            'stroke': '#000000',  # black
            'fill': 'none',  # no fill - just a line
            'stroke-width': '1'  # can also be in form '2mm'
        }
        self.sewing_style = {
            'stroke': '#000000',  # black
            'fill': 'none',  # no fill - just a line
            'stroke-width': '1',  # can also be in form '2mm'
            'stroke-linecap':'butt',
            'stroke-linejoin':'miter',
            'stroke-miterlimit':'10',
            'stroke-dasharray':'9.883,9.883',
            'stroke-dashoffset':'0'
        }

        # Define the list of parameters defined in the .inx file
        self.OptionParser.add_option("-t", "--type", type="string", dest="type", default='perso',
                                     help="Type of template generated")
        self.OptionParser.add_option("-u", "--units", type="string", dest="units", default='cm',
                                     help="Ui units")
        self.OptionParser.add_option("-n", "--neck", type="float", dest="neck", default=88,
                                     help="Width of the neck")
        self.OptionParser.add_option("-s", "--shoulder", type="float", dest="shoulder", default=88,
                                     help="Width shoulder to shoulder")
        self.OptionParser.add_option("--hip", type="float", dest="hip", default=88,
                                     help="Hip measurement")
        self.OptionParser.add_option("-w", "--waist", type="float", dest="waist", default=64,
                                     help="Waist measurement")
        self.OptionParser.add_option("-c", "--chest", type="float", dest="chest", default=80,
                                     help="Chest measurement")
        self.OptionParser.add_option("--hsptochest", type="float", dest="hsp_to_chest", default=80,
                                     help="Lenght HSP to chest")
        self.OptionParser.add_option("--hsptowaist", type="float", dest="hsp_to_waist", default=80,
                                     help="Lenght HSP to waist")
        self.OptionParser.add_option("--hsptohip", type="float", dest="hsp_to_hip", default=80,
                                     help="Lenght HSP to hip")
        self.OptionParser.add_option("-b", "--bicep", type="float", dest="bicep", default=23,
                                     help="Bicep measurement")
        self.OptionParser.add_option("-m", "--sleeve", type="float", dest="sleeve", default=23,
                                     help="Lenght of the sleeve")
        self.OptionParser.add_option("-e", "--ease", type="float", dest="ease", default=2,
                                     help="Amount of ease")
        self.OptionParser.add_option("--active-tab", type="string", dest="active_tab",
                                     default='title', help="Active tab.")

    # ----------------------------------------------------------------#
    #                       UTILITY METHODS
    # ----------------------------------------------------------------#
    def getunittouu(self, param):
        """for 0.48 and 0.91 compatibility"""
        if type(param) is tuple:
            return tuple([self.getunittouu(val) for val in param])
        try:
            return inkex.unittouu(param)
        except AttributeError:
            return self.unittouu(param)

    def calc_unit_factor(self, ui_unit):
        """ return the scale factor for all dimension conversions.
            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        # namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        # doc_units = self.getunittouu(str(1.0) + namedView.get(inkex.addNS('document-units', 'inkscape')))
        unit_factor = self.getunittouu(str(1.0) + ui_unit)
        return unit_factor

    @staticmethod
    def detect_size(optype, mesure_list):
        """Return us standard size corresponding to mesure in cm"""
        sizedic = {
            "fem": {"s": [[0, 90], [0, 68], [0, 84]], "m": [[90, 94], [68, 72], [84, 88]],
                    "l": [[94, 200], [72, 200], [88, 200]]},
            "masc": {"xs": [[0, 94], [0, 78], [0, 90]], "s": [[94, 98], [78, 82], [90, 94]],
                     "m": [[98, 102], [82, 86], [94, 98]], "l": [[102, 106], [86, 90], []], "xl": ()}
        }
        size_found = []
        for standard_size, sizelist in sizedic[optype].items():
            for mesure, pair in zip(mesure_list, sizelist):
                if self.getunittouu(str(pair[1]) + "cm") > mesure >= Patron.getunittouu(str(pair[0]) + "cm"):
                    size_found.append(standard_size)
        return size_found[-1]

    @staticmethod
    def add_text(node, text, transform = '', text_height=12, color='#000000'):
        """Create and insert a single line of text into the svg under node."""
        text_style = {'font-size': '%dpx' % text_height, 'font-style': 'normal', 'font-weight': 'normal',
                      'fill': color, 'font-family': 'Bitstream Vera Sans,sans-serif',
                      'text-anchor': 'middle', 'text-align': 'center'}
        text_attribs = {
            inkex.addNS('label', 'inkscape'): 'Annotation',
            'style': simplestyle.formatStyle(text_style)
        }
        if transform != "translate(0,0)":
            text_attribs['transform']=transform
        text_node = inkex.etree.SubElement(node, inkex.addNS('text', 'svg'), text_attribs)
        text_node.text = text

    # ----------------------------------------------------------------------#
    #                               MAIN
    # ----------------------------------------------------------------------#
    def effect(self):

        # Get Document attribs
        root = self.document.getroot()  # top node in document xml
        docwidth = self.getunittouu(root.get('width'))
        docheight = self.getunittouu(root.get('height'))
        self.doc_center = (str(docwidth / 2), str(docheight / 2))

        # Saved Template drawing
        template_id = self.options.type
        if template_id != "perso":
            self.saved_template(template_id)

        # Gather incoming measurements and convert it to intern unit
        hip = self.getunittouu(str(self.options.hip) + self.options.units)
        waist = self.getunittouu(str(self.options.waist) + self.options.units)
        chest = self.getunittouu(str(self.options.chest) + self.options.units)
        hsp_to_chest = self.getunittouu(str(self.options.hsp_to_chest) + self.options.units)
        hsp_to_waist = self.getunittouu(str(self.options.hsp_to_waist) + self.options.units)
        hsp_to_hip = self.getunittouu(str(self.options.hsp_to_hip) + self.options.units)
        bicep = self.getunittouu(str(self.options.bicep) + self.options.units)
        sleeve = self.getunittouu(str(self.options.sleeve) + self.options.units)

    def front(self, hip, waist, chest, height):
        """ Draw the front piece of the T-shirt template using a turtle """
        # calculate unit factor for units defined in dialog.
        unit_factor = self.calc_unit_factor(self.options.units)
        # Turtle direction
        t = pturtle.pTurtle()
        t.pu()
        t.setpos(computePointInNode(list(self.view_center), self.current_layer))
        t.pd()
        t.fd(hip * unit_factor)
        t.lt(90)
        t.fd(height * unit_factor)
        t.lt(90)
        t.fd(waist * unit_factor)
        t.lt(90)
        t.fd(height * unit_factor)

        # Style definition, cut info and add path to group node

        s = {'stroke-linejoin': 'miter', 'stroke-width': self.path_stroke_width,
             'stroke-opacity': '1.0', 'fill-opacity': '1.0',
             'stroke': self.path_color, 'stroke-linecap': 'butt',
             'fill': self.path_fill}

        inkex.etree.SubElement(self.current_layer,
                               inkex.addNS('path', 'svg'),
                               {'d': t.getPath(), 'style': simplestyle.formatStyle(s)})

        # Add template info
        txtheight = 12
        piece_info = ["T-shirt Simple - Face devant", "Bassin:" + str(hip), "taille:" + str(waist),
                      "poitrine:" + str(chest), "hauteur:" + str(height)]
        [self.add_text(self.topgroup, txt, [0, y * txtheight - 22], txtheight) for y, txt in enumerate(piece_info)]

    # ---------------------------------------------------------------------- #
    #                            SAVED TEMPLATES
    # ---------------------------------------------------------------------- #
    def saved_template(self, template_id):
        """
        Read 'patron.xml' file and get the saved templates data : 
        Paths and Name of it's shapes.
         Then draw the selected template in the document.
        """

        # From user params get the wanted type and size
        type, size = template_id.split('_')

        # Parse the xml file
        template_tree = etree.parse("patron.xml")
        root = template_tree.getroot()

        # Find The selected template
        for template in root.findall("./type[@name='%s']/template[@size='%s']"%(type, size)):
            # Find useful data
            info = 'T-shirt_template_%s_%s' % (type, size)
            transform = template.find('transform')

            # Creation of a main group for the Template
            template_attribs = {
                 inkex.addNS('label', 'inkscape'): info,
                 'transform':transform.text if transform != None else ''
             }
            template_group = inkex.etree.SubElement(self.current_layer, 'g',template_attribs)

            # For each pieces of the template
            for piece in template.findall('piece'):
                # Find useful data
                pieceinfo = info+"_"+piece.find('name').text
                transform = piece.find('transform')

                # Create a group for the piece
                piece_attribs = {
                 inkex.addNS('label', 'inkscape'): pieceinfo,
                 'transform':transform.text if transform != None else ''
                }
                piece_group = inkex.etree.SubElement(template_group, 'g', piece_attribs)

                # Add a text to display the piece info
                self.add_text(piece_group,pieceinfo.replace('_',' '), piece.find('info').text, 15)

                # For each paths of the piece
                for part in piece.findall('part'):
                    # Find useful data
                    name = part.find('name').text
                    partinfo = pieceinfo+"_"+name
                    transform = part.find('transform')

                    # Create a group for the shape
                    part_attribs = {
                     inkex.addNS('label', 'inkscape'): partinfo,
                     'transform':transform.text if transform != None else ''
                    }
                    part_group = inkex.etree.SubElement(piece_group, 'g', part_attribs)

                    # Add the path to the group
                    path_attribs = {
                        inkex.addNS('label', 'inkscape'): partinfo,
                        'style':simplestyle.formatStyle(self.sewing_style if name == "sewing" or name == "lign" else self.offset_style ),
                        'd':part.find('path').text
                    }
                    inkex.etree.SubElement(part_group, inkex.addNS('path','svg'), path_attribs)

if __name__ == '__main__':
    e = Patron()
    e.affect()

    # Notes
