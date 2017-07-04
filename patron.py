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

For reference the user can also render saved standard templates, their paths data are 
 read from the 'patron.xml' file
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


def draw_svg_circle(radius, center, parent, style, transform=''):
    circ_attribs = {
        'style': simplestyle.formatStyle(style),
        'cx': str(center[0]),
        'cy': str(center[1]),
        'r': str(radius),
        'transform': transform
    }
    inkex.etree.SubElement(parent, inkex.addNS('circle', 'svg'), circ_attribs)


def draw_svg_ellipse(start, radius, center, end, parent, style, transform=''):
    sx, sy = start
    rx, ry = radius
    cx, cy = center
    ex, ey = end
    circ_attribs = {
        'style': simplestyle.formatStyle(style),
        'd': 'm {} {} a {} {} {} {} 0 {} {}'.format(sx, sy, rx, ry, cx, cy, ex, ey),
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
        inkex.addNS('label', 'inkscape'): 'cubic curve',
        'transform': transform,
        'd': 'M {} {} c {} {}, {} {}, {} {}'.format(sx, sy, cx, cy, dx, dy, ex, ey)
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
        self.cut_line = {
            'stroke': '#ff0000',  # black
            'fill': 'none',  # no fill - just a line
            'stroke-width': '0.1'  # can also be in form '2mm'
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
                                     help="User interface units")
        self.OptionParser.add_option("--style", type="string", dest="style", default='print',
                                     help="Style of the template")
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
        self.OptionParser.add_option("--hsptochest", type="float", dest="hsp_chest", default=80,
                                     help="Lenght HSP to chest")
        self.OptionParser.add_option("--hsptowaist", type="float", dest="hsp_waist", default=80,
                                     help="Lenght HSP to waist")
        self.OptionParser.add_option("--hsptohip", type="float", dest="hsp_hip", default=80,
                                     help="Lenght HSP to hip")
        self.OptionParser.add_option("-b", "--bicep", type="float", dest="bicep", default=23,
                                     help="Bicep measurement")
        self.OptionParser.add_option("-m", "--sleeve", type="float", dest="sleeve", default=23,
                                     help="Lenght of the sleeve")
        self.OptionParser.add_option("-e", "--ease", type="float", dest="ease", default=3,
                                     help="Amount of ease")
        self.OptionParser.add_option("--neck_front", type="float", dest="neck_front", default=0,
                                     help="Height of the front neck drop")
        self.OptionParser.add_option("--neck_rear", type="float", dest="neck_rear", default=0,
                                     help="Height of the rear neck drop")
        self.OptionParser.add_option("-p", "--shoulder_drop", type="float", dest="shoulder_drop", default=1.5,
                                     help="height of the shoulder")
        self.OptionParser.add_option("-g", "--grid", type="inkbool", dest="grid", default=True,
                                     help="Display the Reference Grid ")
        self.OptionParser.add_option("-v", "--temp", type="inkbool", dest="temp", default=True,
                                     help="Display the template")
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

    def draw_svg_path(self, path_description_list, parent, style, close=True):
        """
        Convert a list of paths descriptions to an svg string path
        then draw the path under parent node .
        a path description is a dictionary <"path type", [(pt1)]>
        :param path_description_list: a list of paths descriptions
        [
        {'l': [(x1, y1),(x2, y2)]},
        {'c': [ (x_ctrl_pt1, y_ctrl_pt1), (x_ctrl_pt2, y_ctrl_pt2), (x_end_pt, y_end_pt) ]},
        {'a': [ (radiusx, radiusy), (0, 0), (x_end_pt, y_end_pt) ]} 
         ]
        :return: the svg string path
        """
        arr = path_description_list
        path = '%s %s' % (arr[0][0], arr[0][1])
        for dic in arr[1:]:
            for descr, pt_list in dic.items():
                path += ' %s ' % descr
                path+= ' '.join([','.join([str(c) for c in pt] if type(pt) is tuple else str(pt)) for pt in pt_list])

        d = "m %s%s" % (path, " z" if close else "")
        # inkex.errormsg(d)
        shape_attribs = {
            'style': simplestyle.formatStyle(style),
            'd': d
        }
        inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), shape_attribs)

    # ------------------------------------------------------------ #
    #                            MAIN
    # ------------------------------------------------------------ #
    def effect(self):
        # Get Document attribs
        root = self.document.getroot()  # top node in document tree
        docwidth = self.getunittouu(root.get('width'))
        docheight = self.getunittouu(root.get('height'))
        self.doc_center = docwidth / 2, docheight / 2

        # Render Saved Template
        template_id = self.options.type
        if template_id != "perso":
            self.saved_template(template_id)
        else:
            # Gather incoming measurements and convert it to internal unit (96dpi pixels)
            ease = self.getunittouu(str(self.options.ease) + self.options.units)
            user = {
                'ease': ease,
                'shoulder_drop': self.getunittouu(str(self.options.shoulder_drop) + self.options.units),
                'neck_front': self.getunittouu(str(self.options.neck_front) + self.options.units),
                'neck_rear': self.getunittouu(str(self.options.neck_rear) + self.options.units),
                'neck': (ease + float(self.getunittouu(str(self.options.neck) + self.options.units))) / 2,
                'shoulder': (ease + float(self.getunittouu(str(self.options.shoulder) + self.options.units))) / 2,
                'hip': (ease + float(self.getunittouu(str(self.options.hip) + self.options.units))) / 4,
                'waist': (ease + float(self.getunittouu(str(self.options.waist) + self.options.units))) / 4,
                'chest': (ease + float(self.getunittouu(str(self.options.chest) + self.options.units))) / 4,
                'hsp_chest': ease + self.getunittouu(str(self.options.hsp_chest) + self.options.units),
                'hsp_waist': self.getunittouu(str(self.options.hsp_waist) + self.options.units),
                'hsp_hip': self.getunittouu(str(self.options.hsp_hip) + self.options.units),
                'bicep': (ease + float(self.getunittouu(str(self.options.bicep) + self.options.units))) / 2,
                'sleeve': self.getunittouu(str(self.options.sleeve) + self.options.units)
            }
            user['shoulder_to_chest'] = user['hsp_chest'] - user['shoulder_drop']
            user['chest_to_waist'] = user['hsp_waist'] - user['hsp_chest']
            user['chest_to_hip'] = user['hsp_hip'] - user['hsp_chest']

            # Main group for the Template
            info = 'Patron_T-shirt_%s_%s_%s' % (self.options.hip, self.options.waist, self.options.chest)
            template_group = inkex.etree.SubElement(self.current_layer, 'g', {inkex.addNS('label', 'inkscape'): info})

            self.main_piece(template_group, user, info + '_front', True)
            self.main_piece(template_group, user, info + '_back', False)

    # -------------------------------------------------------------- #
    #                          FRONT PIECE
    # -------------------------------------------------------------- #
    def main_piece(self, parent, um, info="T-shirt_Template", front=True):
        """
        Render the front piece of the template
        """
        piece_group = inkex.etree.SubElement(parent, 'g',
                                             {inkex.addNS('label', 'inkscape'): info,
                                              'transform': '' if front else 'matrix(-1,0,0,1,-34.745039,0)'})

        # The template main vertexes absolute positions
        neck_drop = um['neck_rear'] if not front else um['neck_front'] if um['neck_front'] > 0 else um['neck']
        vertexes = {
            'neck': (um['neck'], 0),
            'neck_drop': (0, neck_drop),
            'shoulder': (um['shoulder'], um['shoulder_drop']),
            'chest': (um['chest'], um['hsp_chest']),
            'waist': (um['waist'], um['hsp_waist']),
            'hip': (um['hip'], um['hsp_hip'])
        }

        # Template edge paths
        if self.options.temp:
            line_style = self.normal_line if self.options.style == 'print' else self.cut_line
            edge = inkex.etree.SubElement(piece_group, 'g', {inkex.addNS('label', 'inkscape'): info + "_edge"})

            paths = [vertexes['neck_drop']]
            paths.append(self.neckline(um, neck_drop))
            paths.append(self.shoulder_line(um))
            paths.append(self.sleeve_curve(um))
            paths.append(self.waist_curve(um))
            paths.append({'l': [(-um['hip'], 0)]})

            self.draw_svg_path(paths, edge, line_style)

            # draw_svg_ellipse(vertexes['neck_drop'],(um['neck'], neck_drop), (0, 0), (um['neck'], -neck_drop), edge, line_style)
            # draw_svg_line([(0, neck_drop), (0, um['hsp_hip'] - neck_drop)], edge, line_style)
            # draw_svg_line([vertexes['neck'], (um['shoulder'] - um['neck'], um['shoulder_drop'])], edge, line_style)

            # curve_start = vertexes['shoulder']
            # control_point1 = (-self.getunittouu('30mm'), um['shoulder_to_chest'] / 2)
            # control_point2 = (-self.getunittouu('30mm'), um['shoulder_to_chest'])
            # curve_end = (-um['shoulder'] + um['chest'], um['hsp_chest'] - um['shoulder_drop'])
            # draw_svg_cubic_curve(curve_start, control_point1, control_point2, curve_end, edge, line_style)

            # curve_start = vertexes['chest']
            # control_point1 = (-(um['chest'] - um['waist']), um['chest_to_waist'])
            # control_point2 = (-(um['chest'] - um['hip']), 0.75 * um['chest_to_hip'])
            # curve_end = (-um['chest'] + um['hip'], um['chest_to_hip'])
            # draw_svg_cubic_curve(curve_start, control_point1, control_point2, curve_end, edge, line_style)

            # draw_svg_line([vertexes['hip'], (-um['hip'], 0)], edge, line_style)

        # The Template structure reference
        if self.options.grid:
            reference = inkex.etree.SubElement(piece_group, 'g',
                                               {inkex.addNS('label', 'inkscape'): info + "_structure"})

            draw_svg_line([(0, 0), (0, um['hsp_hip'])], reference, self.doted_line)
            draw_svg_line([(0, 0), (um['neck'], 0)], reference, self.doted_line)
            draw_svg_line([(um['neck'], 0), (0, um['hsp_hip'])], reference, self.doted_line)
            draw_svg_line([(0, um['shoulder_drop']), (um['shoulder'], 0)], reference, self.doted_line)
            draw_svg_line([(0, um['hsp_chest']), (um['chest'], 0)], reference, self.doted_line)
            draw_svg_line([(0, um['hsp_waist']), (um['waist'], 0)], reference, self.doted_line)
            draw_svg_line([(0, um['hsp_hip']), (um['hip'], 0)], reference, self.doted_line)

            for name, vertex in vertexes.items():
                draw_svg_circle(4, vertex, reference, self.normal_line)
        """
                    attr = {'style':simplestyle.formatStyle(s),
                       inkex.addNS('type','sodipodi'):   'inkscape:offset',
                       inkex.addNS('radius','inkscape'):   '5',
                       inkex.addNS('original','inkscape'):   d
                    }
        """

    def neckline(self, um, neckdrop):
        return {'a': [(um['neck'], neckdrop), 0, 0, 0, (um['neck'], -neckdrop)]}

    def shoulder_line(self, um):
        return {'l': [(um['shoulder'] - um['neck'], um['shoulder_drop'])]}

    def sleeve_curve(self, um):
        ctrl_p1 = (-self.getunittouu('30mm'), um['shoulder_to_chest'] / 2)
        ctrl_p2 = (-self.getunittouu('30mm'), um['shoulder_to_chest'])
        curve_end = (-um['shoulder'] + um['chest'], um['hsp_chest'] - um['shoulder_drop'])
        return {'c': [ctrl_p1, ctrl_p2, curve_end]}

    def waist_curve(self, um):
        ctrl_p1 = (-(um['chest'] - um['waist']), um['chest_to_waist'])
        ctrl_p2 = (-(um['chest'] - um['hip']), 0.75 * um['chest_to_hip'])
        curve_end = (-um['chest'] + um['hip'], um['chest_to_hip'])
        return {'c': [ctrl_p1, ctrl_p2, curve_end]}

    # ---------------------------------------------------------------------- #
    #                        RENDER SAVED TEMPLATES
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
                    line_syle = self.normal_line if self.options.style == 'print' or label != 'offset' else self.cut_line
                    path_attribs = {
                        inkex.addNS('label', 'inkscape'): partinfo,
                        'style': simplestyle.formatStyle(line_syle),
                        'd': part.find('path').text
                    }
                    inkex.etree.SubElement(part_group, inkex.addNS('path', 'svg'), path_attribs)


if __name__ == '__main__':
    e = Patron()
    e.affect()

    # Notes
