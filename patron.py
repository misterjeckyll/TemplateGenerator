#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2017 William Pantry pantryw@gmail.com
-----------------------------------------------
                  DESCRIPTION
-----------------------------------------------
This extension render a t-shirt svg template, constructed from the user body measurements.
The rendered template is used as a support for sewing a T-shirt with the user's morphology.

The svg template can then be printed with a plotter-tracer (or any kind of printer)
 on one or two (for the biggest sizes) A0 Paper Page.
The SVG template can also be used to directly cut the clothing with a laser cutter.

-----------------------------------------------
                    LICENSE
-----------------------------------------------
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import xml.etree.ElementTree as Etree
from math import pi

import inkex
import simplestyle

__version__ = '1'

inkex.localize()


# ---------------------------------------------------------------- #
#                       UTILITY FUNCTIONS
# ---------------------------------------------------------------- #
def add_text(parent, text, transform='', text_height=12, color='#000000'):
    """
        Create and insert a single line of text into the svg document under parent.
    """
    text_style = {'font-size': '%dpx' % text_height, 'font-style': 'normal', 'font-weight': 'normal',
                  'fill': color, 'font-family': 'Bitstream Vera Sans,sans-serif',
                  'text-anchor': 'middle', 'text-align': 'center'}

    text_attribs = {
        inkex.addNS('label', 'inkscape'): 'Annotation',
        'style': simplestyle.formatStyle(text_style)
    }
    if transform != "translate(0,0)":
        text_attribs['transform'] = transform
    text_node = inkex.etree.SubElement(parent, inkex.addNS('text', 'svg'), text_attribs)
    text_node.text = text


def draw_svg_line(points_list, parent, style):
    """
        Draw an SVG line segment between the given points under parent
    """
    line_attribs = {'style': simplestyle.formatStyle(style),
                    inkex.addNS('label', 'inkscape'): 'line',
                    'd': to_path_string(points_list, False)}

    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), line_attribs)


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


def draw_svg_ellipse(radius, center, parent, style, start_end=(0, 2 * pi), transform=''):
    rx, ry = radius
    cx, cy = center
    circ_attribs = {
        'style': simplestyle.formatStyle(style),
        inkex.addNS('cx', 'sodipodi'): str(cx),
        inkex.addNS('cy', 'sodipodi'): str(cy),
        inkex.addNS('rx', 'sodipodi'): str(rx),
        inkex.addNS('ry', 'sodipodi'): str(ry),
        inkex.addNS('start', 'sodipodi'): str(start_end[0]),
        inkex.addNS('end', 'sodipodi'): str(start_end[1]),
        inkex.addNS('open', 'sodipodi'): 'true',  # all ellipse sectors we will draw are open
        inkex.addNS('type', 'sodipodi'): 'arc',
        'transform': transform
    }
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), circ_attribs)


def draw_svg_cubic_curve(curve_start, pt1, pt2, curve_end, parent, style, transform=''):
    sx, sy = curve_start
    cx, cy = pt1
    dx, dy = pt2
    ex, ey = curve_end
    curve_attribs = {
        'style': simplestyle.formatStyle(style),
        inkex.addNS('label','inkscape'):'cubic curve',
        'transform': transform,
        'd':'M {} {} c {} {}, {} {}, {} {}'.format(sx, sy, cx, cy, dx, dy, ex, ey)
    }
    inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), curve_attribs)


def to_path_string(arr, close=True):
    return "m %s%s" % (' '.join([','.join([str(c) for c in pt]) for pt in arr]), " z" if close else "")


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
        Patron render the paths of a basic T-shirt template from user measurements.
        Printed, this Svg template is used as a support for sewing a t-shirt 
        with the correct morphology.
    """

    def __init__(self):
        """
            Define how the options are mapped from the inx file
            and initialize class attributes
        """
        inkex.Effect.__init__(self)

        self.doc_center = None
        self.normal_line = {
            'stroke': '#000000',  # black
            'fill': 'none',  # no fill - just a line
            'stroke-width': '1'  # can also be in form '2mm'
        }
        self.doted_line = {
            'stroke': '#000000',  # black
            'fill': 'none',  # no fill - just a line
            'stroke-width': '1',  # can also be in form '2mm'
            'stroke-linecap': 'butt',
            'stroke-linejoin': 'miter',
            'stroke-miterlimit': '10',
            'stroke-dasharray': '9.883,9.883',
            'stroke-dashoffset': '0'
        }

        # Define the list of parameters defined in the .inx file
        self.OptionParser.add_option("-t", "--type", type="string", dest="type", default='perso',
                                     help="Type of template rendered")
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
        """ 
            return the scale factor for all dimension conversions.
            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        # namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        # doc_units = self.getunittouu(str(1.0) + namedView.get(inkex.addNS('document-units', 'inkscape')))
        unit_factor = self.getunittouu(str(1.0) + ui_unit)
        return unit_factor

    # ------------------------------------------------------------ #
    #                            MAIN
    # ------------------------------------------------------------ #
    def effect(self):

        # Get Document attribs
        root = self.document.getroot()  # top node in document tree
        docwidth = self.getunittouu(root.get('width'))
        docheight = self.getunittouu(root.get('height'))
        self.doc_center = docwidth / 2, docheight / 2

        # Saved Template drawing
        template_id = self.options.type
        if template_id != "perso":
            self.saved_template(template_id)
        else:
            # Gather incoming measurements and convert it to internal unit (96dpi pixels)
            ease = self.getunittouu(str(self.options.ease) + self.options.units)
            user_measurements = {
                'ease': ease,
                'shoulder_drop':self.getunittouu('1.5cm'),
                'half_neck': (ease + float(self.getunittouu(str(self.options.neck) + self.options.units))) / 2,
                'half_shoulder': (ease + float(self.getunittouu(str(self.options.shoulder) + self.options.units))) / 2,
                'quarter_hip': (ease + float(self.getunittouu(str(self.options.hip) + self.options.units))) / 4,
                'quarter_waist': (ease + float(self.getunittouu(str(self.options.waist) + self.options.units))) / 4,
                'quarter_chest': (ease + float(self.getunittouu(str(self.options.chest) + self.options.units))) / 4,
                'hsp_to_chest': ease + self.getunittouu(str(self.options.hsp_to_chest) + self.options.units),
                'hsp_to_waist': self.getunittouu(str(self.options.hsp_to_waist) + self.options.units),
                'hsp_to_hip': self.getunittouu(str(self.options.hsp_to_hip) + self.options.units),
                'bicep_half': (ease + float(self.getunittouu(str(self.options.bicep) + self.options.units))) / 2,
                'sleeve': self.getunittouu(str(self.options.sleeve) + self.options.units)
            }
            # Main group for the Template
            info = 'Patron_T-shirt_%s_%s_%s' % (self.options.hip, self.options.waist, self.options.chest)
            template_group = inkex.etree.SubElement(self.current_layer, 'g', {inkex.addNS('label', 'inkscape'): info})

            self.front(template_group, user_measurements, info)

    # -------------------------------------------------------------- #
    #                          FRONT PIECE
    # -------------------------------------------------------------- #
    def front(self, parent, um, info="T-shirt_Template"):
        """
        Render the front piece of the template
        """
        front_group = inkex.etree.SubElement(parent, 'g', {inkex.addNS('label', 'inkscape'): info + "_front"})

        Reference = inkex.etree.SubElement(front_group, 'g', {inkex.addNS('label', 'inkscape'): info + "_structure"})
        edge = inkex.etree.SubElement(front_group, 'g', {inkex.addNS('label', 'inkscape'): info + "_edge"})

        # The Template structure reference
        draw_svg_line([(0, 0), (0, um['hsp_to_hip'])], Reference, self.doted_line)
        draw_svg_line([(0, 0), (um['half_neck'], 0)], Reference, self.doted_line)
        draw_svg_line([(um['half_neck'], 0), (0, um['hsp_to_hip'])], Reference, self.doted_line)
        draw_svg_line([(0, um['shoulder_drop']), (um['half_shoulder'], 0)], Reference, self.doted_line)
        draw_svg_line([(0, um['hsp_to_chest']), (um['quarter_chest'], 0)], Reference, self.doted_line)
        draw_svg_line([(0, um['hsp_to_waist']), (um['quarter_waist'], 0)], Reference, self.doted_line)
        draw_svg_line([(0, um['hsp_to_hip']), (um['quarter_hip'], 0)], Reference, self.doted_line)

        # The template main vertexes absolute positions
        vertexes = {
            'neck': (um['half_neck'], 0),
            'shoulder': (um['half_shoulder'], um['shoulder_drop']),
            'chest': (um['quarter_chest'], um['hsp_to_chest']),
            'waist': (um['quarter_waist'], um['hsp_to_waist']),
            'hip': (um['quarter_hip'], um['hsp_to_hip'])
        }
        for name, vertex in vertexes.items():
            draw_svg_ellipse((3, 3), (vertex[0], vertex[1]), Reference, self.normal_line)

        # Template edge paths
        # neck_drop = self.getunittouu('5cm')
        draw_svg_ellipse((um['half_neck'], um['half_neck']), (0, 0), edge, self.normal_line, (0, pi/2))
        draw_svg_line([(0, um['half_neck']), (0,um['hsp_to_hip']-um['half_neck'])], edge, self.normal_line)
        draw_svg_line([vertexes['neck'],(um['half_shoulder']-um['half_neck'],um['shoulder_drop'])], edge, self.normal_line)

        curve_start = vertexes['shoulder']
        control_point1 = (-um['quarter_chest']/4, um['hsp_to_chest']/2)
        control_point2 = (-um['quarter_chest']/4, um['hsp_to_chest']*0.75)
        curve_end = (-um['half_shoulder']+um['quarter_chest'], um['hsp_to_chest']-um['shoulder_drop'])
        draw_svg_cubic_curve(curve_start, control_point1, control_point2, curve_end, edge, self.normal_line)

    # ---------------------------------------------------------------------- #
    #                         RENDER SAVED TEMPLATES
    # ---------------------------------------------------------------------- #
    def saved_template(self, template_id):
        """
            Read 'patron.xml' file and get the saved templates data
            Then render the selected template in the document.
        """

        # From user params get the wanted type and size
        category, size = template_id.split('_')

        # Parse the xml file
        template_tree = Etree.parse("patron.xml")
        root = template_tree.getroot()

        # Find The selected template
        for template in root.findall("./type[@name='%s']/template[@size='%s']" % (category, size)):
            # Find useful data
            info = 'T-shirt_template_%s_%s' % (category, size)
            transform = template.find('transform')

            # Creation of a main group for the Template
            template_attribs = {
                inkex.addNS('label', 'inkscape'): info,
                'transform': transform.text if transform is not None else ''
            }
            template_group = inkex.etree.SubElement(self.current_layer, 'g', template_attribs)

            # For each pieces of the template
            for piece in template.findall('piece'):
                # Find useful data
                pieceinfo = info + "_" + piece.find('name').text
                transform = piece.find('transform')

                # Create a group for the piece
                piece_attribs = {
                    inkex.addNS('label', 'inkscape'): pieceinfo,
                    'transform': transform.text if transform is not None else ''
                }
                piece_group = inkex.etree.SubElement(template_group, 'g', piece_attribs)

                # Add a text to display the piece info
                add_text(piece_group, pieceinfo.replace('_', ' '), piece.find('info').text, 15)

                # For each paths of the piece
                for part in piece.findall('part'):
                    # Find useful data
                    label = part.find('name').text
                    partinfo = pieceinfo + "_" + label
                    transform = part.find('transform')

                    # Create a group for the shape
                    part_attribs = {
                        inkex.addNS('label', 'inkscape'): partinfo,
                        'transform': transform.text if transform is not None else ''
                    }
                    part_group = inkex.etree.SubElement(piece_group, 'g', part_attribs)

                    # Add the path to the group
                    path_attribs = {
                        inkex.addNS('label', 'inkscape'): partinfo,
                        'style': simplestyle.formatStyle(
                            self.doted_line if label == "sewing" or label == "lign" else self.normal_line),
                        'd': part.find('path').text
                    }
                    inkex.etree.SubElement(part_group, inkex.addNS('path', 'svg'), path_attribs)


if __name__ == '__main__':
    e = Patron()
    e.affect()

    # Notes
