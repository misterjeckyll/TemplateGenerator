# encoding: utf-8
import math
import inkex
import simplestyle
#------------------------------------------------------------------#
# Exception handling
#------------------------------------------------------------------#
class BoxGenrationError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class BoxEffect():
# ------------------------------------------------------------------#
# Path format and utility functions
# ------------------------------------------------------------------#
    def add(self,vectorlist,id,x_pos,y_pos,bg,fg):
        """add the svg representation of a list of vectors
        """
        self.list_of_paths.append(self.getPath(self.toPathString(self.mm2u(vectorlist)),id,x_pos,y_pos,bg,fg))
        
    def _rotate_path(self, points, direction):
        if direction == 1:
            return [[-point[1], point[0]] for point in points]

        elif direction == 2:
            return [[-point[0], -point[1]] for point in points]

        elif direction == 3:
            return [[point[1], -point[0]] for point in points]
        else:
            return points

    def mm2u(self, arr):
        '''
        Translate a value or an array of values form 'mm' to document unit
        '''
        if type(arr) is list:
            return [self.mm2u(coord) for coord in arr]
        else:
            try:# for 0.48 and 0.91 compatibility
                return inkex.unittouu("%smm" % arr)
            except AttributeError:
                return self.unittouu("%smm" % arr)

    def toPathString(self, arr, end=" z"):
        return "m %s%s" % (' '.join([','.join([str(c) for c in pt]) for pt in arr]), end)

    def getPath(self, path, path_id, _x, _y, bg, fg):
        style = {'stroke': fg,
                 'fill': bg if(bg) else 'none',
                 'stroke-width': 0.1}
        return {
            'style': simplestyle.formatStyle(style),
            'id': path_id,
            'transform': "translate(%s,%s)" % (_x, _y),
            'd': path
        }
# ------------------------------------------------------------------#
# Hole for tabbed paths
# ------------------------------------------------------------------#
    def holes(self,length, tab_width,thickness,direction,prefix,_x,_y,bg,fg,width,depth,height,backlash,stack=False,inverted=True):

        ### Calcultate tab size and number
        nb_tabs = math.floor(length / tab_width)
        nb_tabs = int(nb_tabs - 1 + (nb_tabs % 2))
        tab_real_width = length / nb_tabs
        # Check if no inconsistency on tab size and number
        if (tab_real_width <= thickness * 1.5):
            raise BoxGenrationError("Attention les encoches resultantes (%s mm) ne sont pas assez larges au vue de l'epasseur de votre materiaux. Merci d'utiliser une taille d'encoches coherente avec votre boite" % tab_real_width)
        #inkex.debug("Pour une largeur de %s et des encoches de %s => Nombre d'encoches : %s Largeur d'encoche : %s" % (length, tab_width, nb_tabs, tab_real_width))

        hrect = [[backlash, 0],[0,thickness],[tab_real_width+backlash,0],[0,-thickness]]

        if(not direction):
            for i in range(1,nb_tabs+1):
                if (i % 2 == inverted):
                    self.add(hrect,'%s_Horizontal_Hole' % prefix,_x + self.mm2u((i-inverted) * tab_real_width-0.5*backlash*(i==0)),_y, bg, fg)
        else:
            for i in range(1,nb_tabs+1):
                if (i % 2 == 0):
                    self.add(self._rotate_path(hrect,1),'%s_Vertical_Hole' % prefix,_x , _y+ self.mm2u((i-inverted)*tab_real_width-0.5*backlash*(i==0)), bg, fg)

# ------------------------------------------------------------------#
# Tabbed paths
# ------------------------------------------------------------------#
    def tabs(self, length, tab_width, thickness, direction=0, **args):
        '''
             * Genere les elements d'un polygone
             * svg pour des encoche d'approximativement
             * <tab_width>, sur un longueur de <length>,
             * pour un materiau d'epaisseur <thickness>.
             *
             * Options :
             *  - direction : 0 haut de la face, 1 droite de la face, 2 bas de la face, 3 gauche de la face.
             *  - firstUp : Indique si l'on demarre en haut d'un crenau (true) ou en bas du crenau (false - defaut)
             *  - lastUp : Indique si l'on fin en haut d'un crenau (true) ou en bas du crenau (false - defaut)
        '''
        # Calcultate tab size and number
        nb_tabs = math.floor(length / tab_width)
        nb_tabs = int(nb_tabs - 1 + (nb_tabs % 2))
        tab_real_width = length / nb_tabs

        # Check if no inconsistency on tab size and number
        #print("Pour une largeur de %s et des encoches de %s => Nombre d'encoches : %s Largeur d'encoche : %s" % (length, tab_width, nb_tabs, tab_real_width))
        if (tab_real_width <= thickness * 1.5):
            raise BoxGenrationError("Attention les encoches resultantes (%s mm) ne sont pas assez larges au vue de l'epasseur de votre materiaux. Merci d'utiliser une taille d'encoches coherente avec votre boite" % tab_real_width)
    #     if (nb_tabs <= 1):
    #         raise BoxGenrationError("Attention vous n'aurez aucune encoche sur cette longeur, c'est une mauvaise idée !!! Indiquez une taill d'encoche correcte pour votre taille de boite")

        return self._rotate_path(self._generate_tabs_path(tab_real_width, nb_tabs, thickness, direction=direction, **args), direction)

    def _generate_tabs_path(self, tab_width, nb_tabs, thickness, cutOff=False, inverted=False, firstUp=False, lastUp=False, backlash=0, **args):
        # if (cutOff):
            #print("Generation d'un chemin avec l'option cuttOff")
        # else:
            #print("Generation d'un chemin sans l'option cuttOff")

        points = []
        for i in range(1, nb_tabs + 1):
            if(inverted):
                if(i % 2 == 1):  # gap
                    if(not firstUp or i != 1):
                        points.append([0, thickness])

                    if(i == 1 or i == nb_tabs):
                        points.append([tab_width - [0, thickness][cutOff] - (0.5 * backlash), 0])
                    else:
                        points.append([tab_width - backlash, 0])

                    if (i != nb_tabs or not lastUp):
                        points.append([0, -thickness])

                else:  # tab
                    points.append([tab_width + backlash, 0])

            else:
                if(i % 2 == 1):  # tab
                    if(not firstUp or i != 1):
                        points.append([0, -thickness])

                    if(i == 1 or i == nb_tabs):
                        points.append([tab_width - [0, thickness][cutOff] + (0.5 * backlash), 0])
                    else:
                        points.append([tab_width + backlash, 0])

                    if (i != nb_tabs or not lastUp):
                        points.append([0, thickness])

                else:  # gap
                    points.append([tab_width - backlash, 0])

        return points
# ------------------------------------------------------------------#
# Shape of each box pieces
# ------------------------------------------------------------------#
### Bottom/top

    def _stackable_bottom(self, width, depth, tab_width, thickness, backlash):
        points = [[thickness,-thickness],[thickness,0]]
        points.extend(self.tabs(width-4*thickness, tab_width, thickness,direction=0,backlash=backlash,firstUp=False,lastUp=False))
        points.extend([[thickness,0],[0,thickness]])
        points.extend(self.tabs(depth-4*thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=False,lastUp=False))
        points.extend([[0,thickness],[-thickness,0]])
        points.extend(self.tabs(width-4*thickness, tab_width, thickness,direction=2,backlash=backlash,firstUp=False,lastUp=False))
        points.extend([[-thickness,0],[0,-thickness]])
        points.extend(self.tabs(depth-4*thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=False,lastUp=False))
        return points

    def _bottom(self, width, depth, tab_width, thickness, backlash):
        points = [[0, 0]]
        points.extend(self.tabs(width, tab_width, thickness,direction=0,backlash=backlash,firstUp=True,lastUp=True))
        points.extend(self.tabs(depth, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True))
        points.extend(self.tabs(width, tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True))
        points.extend(self.tabs(depth, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True))
        return points
### Front
    def _front_without_top(self, width, height, tab_width, thickness, backlash):
        # print("_front_without_top")
        points = [[0, 0], [width, 0]]
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True))
        points.extend(self.tabs(width,tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True))
        return points

    def _front_with_top(self, width, height, tab_width, thickness, backlash):
        # print("_front_with_top")
        points = [[0, thickness]]
        points.extend(self.tabs(width, tab_width, thickness,direction=0, backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(height - (thickness * 2), tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True))
        points.extend(self.tabs(width, tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(height - (thickness * 2), tab_width, thickness, direction=3,backlash=backlash,firstUp=True,lastUp=True))
        return points

    def _stackable_front_without_top(self, width, height, tab_width, thickness, backlash):
        stackheight=thickness
        stackoffset=width/10
        points = [[0, 0], [stackoffset, 0],[0,-stackheight],[width-2*stackoffset,0],[0,stackheight],[stackoffset,0]]
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True))
        points.extend([[0,2*thickness+stackheight],[-stackoffset,0],[0,-stackheight],[-width +2*stackoffset, 0],[0,stackheight],[-stackoffset,0],[0,-stackheight-2*thickness]])
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True))
        return points
### Side

    def _side_without_top(self, depth, height, tab_width, thickness, backlash):
        # print("_side_without_top")
        points = [[thickness, 0], [depth - (4 * thickness), 0]]
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(depth, tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True,cutOff=True))
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        return points

    def _side_with_top(self, depth, height, tab_width, thickness, backlash):
        # print("_side_with_top")
        points = [[thickness, thickness]]
        points.extend(self.tabs(depth, tab_width, thickness,direction=0,backlash=backlash,firstUp=True,lastUp=True,inverted=True,cutOff=True))
        points.extend(self.tabs(height - (2 * thickness), tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(depth, tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True,cutOff=True))
        points.extend(self.tabs(height - (2 * thickness), tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        return points

    def _stackable_side_without_top(self, depth, height, tab_width, thickness, backlash):
        # print("_side_without_top")
        stackheight=thickness
        stackoffset=depth/10
        points = [[stackoffset, 0],[0,-stackheight],[depth-2*stackoffset-2*thickness,0],[0,stackheight],[stackoffset,0]]
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend([[0,2*thickness+stackheight],[-stackoffset,0],[0,-stackheight],[-depth + (2 * thickness)+2*stackoffset, 0],[0,stackheight],[-stackoffset,0],[0,-stackheight-2*thickness]])
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        return points

    def _box_with_top(self, prefix, _x, _y, bg, fg, width, depth, height, tab_size, thickness, backlash):
        paths = []
        self.add(self._bottom(width, depth, tab_size, thickness, backlash), '%s_bottom' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(1 * thickness), bg, fg)
        self.add(self._bottom(width, depth, tab_size, thickness, backlash), '%s_top' % prefix, _x + self.mm2u(2 * thickness + width), _y + self.mm2u(1 * thickness), bg, fg)
        self.add(self._front_with_top(width, height, tab_size, thickness, backlash), '%s_font' % prefix, _x + self.mm2u(2 * thickness + width), _y + self.mm2u(2 * thickness + depth), bg, fg)
        self.add(self._front_with_top(width, height, tab_size, thickness, backlash), '%s_back' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(2 * thickness + depth), bg, fg)
        self.add(self._side_with_top(depth, height, tab_size, thickness, backlash), '%s_left_side' %  prefix, _x + self.mm2u(2 * thickness + depth), _y + self.mm2u(3 * thickness + depth + height), bg, fg)
        self.add(self._side_with_top(depth, height, tab_size, thickness, backlash), '%s_right_side' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(3 * thickness + depth + height), bg, fg)
        

    def _box_without_top(self, prefix, _x, _y, bg, fg, width, depth, height, tab_size, thickness, backlash):
        paths = []
        self.add(self._bottom(width, depth, tab_size, thickness, backlash), '%s_bottom' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(1 * thickness), bg, fg)
        self.add(self._front_without_top(width, height, tab_size, thickness, backlash), '%s_font' % prefix, _x + self.mm2u(2 * thickness + width), _y + self.mm2u(2 * thickness + depth), bg, fg)
        self.add(self._front_without_top(width, height, tab_size, thickness, backlash), '%s_back' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(2 * thickness + depth), bg, fg)
        self.add(self._side_without_top(depth, height, tab_size, thickness, backlash), '%s_left_side' % prefix, _x + self.mm2u(2 * thickness + depth), _y + self.mm2u(3 * thickness + depth + height), bg, fg)
        self.add(self._side_without_top(depth, height, tab_size, thickness, backlash), '%s_right_side' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(3 * thickness + depth + height), bg, fg)
        
#------------------------------------------------------------------#
# Main Shapes of selected type of box
#------------------------------------------------------------------#
    def _box_without_top_selection(self, layout,prefix, _x, _y, bg, fg, width, depth, height, tab_size, thickness, backlash,segment_offset,layeroffset,lid):
        """
        Draw an open Box with internal parts or not 
        :param segment_offset: dictionnary of the offset of each internal part to draw
        -> {'H':[y_offset_horizontal_segment1,y_offset_horizontal_segment2,...],'V':[x_offset_vertical_segment1,...]}
        """
        
        ### Draw each sides of the box

        if(lid):
            layeroffset=thickness if layeroffset<thickness else layeroffset
            self.lid(prefix,_x,_y,layout,width,depth,thickness,bg,fg)
        self.add(self._bottom(width, depth, tab_size, thickness, backlash),'%s_bottom' % prefix,_x + self.mm2u(layout['bottom_pos'][0]),_y + self.mm2u(layout['bottom_pos'][1]), bg, fg)
        self.add(self._front_without_top(width, height, tab_size, thickness, backlash),'%s_front' % prefix,_x + self.mm2u(layout['front_pos'][0]),_y + self.mm2u(layout['front_pos'][1]), bg, fg)
        self.add(self._front_without_top(width, height, tab_size, thickness, backlash),'%s_back' % prefix,_x + self.mm2u(layout['back_pos'][0]),_y + self.mm2u(layout['back_pos'][1]), bg, fg)
        self.add(self._side_without_top(depth, height, tab_size, thickness, backlash),'%s_left_side' % prefix,_x + self.mm2u(layout['left_pos'][0]),_y + self.mm2u(layout['left_pos'][1]), bg, fg)
        self.add(self._side_without_top(depth, height, tab_size, thickness, backlash),'%s_right_side' % prefix,_x + self.mm2u(layout['right_pos'][0]),_y + self.mm2u(layout['right_pos'][1]), bg,fg)

        height = height - layeroffset
        self.box_layer(layout,prefix, _x, _y, bg, fg, width, depth,height-thickness, tab_size, thickness, backlash,segment_offset)
        for horizontal_offset in segment_offset['H']:
            #inkex.debug("xpos:%s - horizontal_offset:%s - "%(layout['left_pos'][0],horizontal_offset))
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_left",_x+ self.mm2u(layout['left_pos'][0]+horizontal_offset-1.5*thickness),_y+ self.mm2u(layout['left_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_right",_x+ self.mm2u(layout['right_pos'][0]+depth-horizontal_offset-1.5*thickness),_y+ self.mm2u(layout['right_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)
        for vertical_offset in segment_offset['V']:
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_front",_x+ self.mm2u(layout['front_pos'][0]+vertical_offset+0.5*thickness),_y+ self.mm2u(layout['front_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_back",_x+ self.mm2u(layout['back_pos'][0]+width-vertical_offset+0.5*thickness),_y+ self.mm2u(layout['back_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)


    def _box_with_top_selection(self, layout,prefix, _x, _y, bg, fg, width, depth, height, tab_size, thickness, backlash,segment_offset,layeroffset):

        ### Draw each sides of the box

        self.add(self._bottom(width, depth, tab_size, thickness, backlash),'%s_bottom' % prefix,_x + self.mm2u(layout['bottom_pos'][0]),_y + self.mm2u(layout['bottom_pos'][1]), bg, fg)
        self.add(self._bottom(width, depth, tab_size, thickness, backlash),'%s_top' % prefix,_x + self.mm2u(layout['top_pos'][0]),_y + self.mm2u(layout['top_pos'][1]), bg, fg)
        self.add(self._front_with_top(width, height, tab_size, thickness, backlash),'%s_front' % prefix,_x + self.mm2u(layout['front_pos'][0]),_y + self.mm2u(layout['front_pos'][1]), bg, fg)
        self.add(self._front_with_top(width, height, tab_size, thickness, backlash),'%s_back' % prefix,_x + self.mm2u(layout['back_pos'][0]),_y + self.mm2u(layout['back_pos'][1]), bg, fg)
        self.add(self._side_with_top(depth, height, tab_size, thickness, backlash),'%s_left_side' % prefix,_x + self.mm2u(layout['left_pos'][0]),_y + self.mm2u(layout['left_pos'][1]), bg, fg)
        self.add(self._side_with_top(depth, height, tab_size, thickness, backlash),'%s_right_side' % prefix,_x + self.mm2u(layout['right_pos'][0]),_y + self.mm2u(layout['right_pos'][1]), bg,fg)
        height = height - layeroffset
        self.box_layer(layout,prefix, _x, _y, bg, fg, width, depth,height-2*thickness, tab_size, thickness, backlash,segment_offset)
        for horizontal_offset in segment_offset['H']:
            #inkex.debug("xpos:%s - horizontal_offset:%s - "%(layout['left_pos'][0],horizontal_offset))
            self.holes(height-2*thickness,tab_size,thickness,1,prefix+"_left",_x+ self.mm2u(layout['left_pos'][0]+horizontal_offset+0.5*thickness),_y+ self.mm2u(layout['left_pos'][1]+layeroffset+thickness),bg,fg,width,depth,height,backlash)
            self.holes(height-2*thickness,tab_size,thickness,1,prefix+"_right",_x+ self.mm2u(layout['right_pos'][0]+depth-horizontal_offset+0.5*thickness),_y+ self.mm2u(layout['right_pos'][1]+layeroffset+thickness),bg,fg,width,depth,height,backlash)
        for vertical_offset in segment_offset['V']:
            self.holes(height-2*thickness,tab_size,thickness,1,prefix+"_front",_x+ self.mm2u(layout['front_pos'][0]+vertical_offset+0.5*thickness),_y+ self.mm2u(layout['front_pos'][1]+layeroffset+thickness),bg,fg,width,depth,height,backlash)
            self.holes(height-2*thickness,tab_size,thickness,1,prefix+"_back",_x+ self.mm2u(layout['back_pos'][0]+width-vertical_offset+0.5*thickness),_y+ self.mm2u(layout['back_pos'][1]+layeroffset+thickness),bg,fg,width,depth,height,backlash)


    def _box_without_top_stackable_selection(self, layout,prefix, _x, _y, bg, fg, width, depth, height, tab_size, thickness, backlash,segment_offset,layeroffset,lid):

        ### Adjust layout position to stack height

        layout['left_pos'][1] += 3*thickness
        layout['right_pos'][1] += 3*thickness
        layout['H_layer_pos'][1] += 5 * thickness
        layout['V_layer_pos'][1] += 5 * thickness

        ### Draw each side of the box
        
        if(lid):
            layeroffset=thickness if layeroffset<thickness else layeroffset
            self.add(self.lid(prefix,_x,_y,layout,width,depth,thickness,bg,fg))

        self.add(self._stackable_bottom(width, depth, tab_size, thickness, backlash),'%s_bottom' % prefix,_x + self.mm2u(layout['bottom_pos'][0]),_y + self.mm2u(layout['bottom_pos'][1]), bg, fg)

        self.add(self._stackable_front_without_top(width, height, tab_size, thickness, backlash),'%s_front' % prefix,_x + self.mm2u(layout['front_pos'][0]),_y + self.mm2u(layout['front_pos'][1]), bg, fg)
        self.holes(width-(4*thickness),tab_size,thickness,0,prefix+"_front",_x+ self.mm2u(layout['front_pos'][0]+2*thickness),_y+ self.mm2u(layout['front_pos'][1]+height-thickness),bg,fg,width,depth,height,backlash,stack=True)

        self.add(self._stackable_front_without_top(width, height, tab_size, thickness, backlash),'%s_back' % prefix,_x + self.mm2u(layout['back_pos'][0]),_y + self.mm2u(layout['back_pos'][1]), bg, fg)
        self.holes(width-(4*thickness),tab_size,thickness,0,prefix+"_back",_x+ self.mm2u(layout['back_pos'][0]+2*thickness),_y+ self.mm2u(layout['front_pos'][1]+height-thickness),bg,fg,width,depth,height,backlash,stack=True)

        self.add(self._stackable_side_without_top(depth, height, tab_size, thickness, backlash),'%s_left_side' % prefix,_x + self.mm2u(layout['left_pos'][0]),_y + self.mm2u(layout['left_pos'][1]), bg, fg)
        self.holes(depth-(4*thickness),tab_size,thickness,0,prefix+"_left",_x+ self.mm2u(layout['left_pos'][0]+thickness),_y+ self.mm2u(layout['left_pos'][1]+height-thickness),bg,fg,width,depth,height,backlash,stack=True)

        self.add(self._stackable_side_without_top(depth, height, tab_size, thickness, backlash),'%s_right_side' % prefix,_x + self.mm2u(layout['right_pos'][0]),_y + self.mm2u(layout['right_pos'][1]), bg,fg)
        self.holes(depth-(4*thickness),tab_size,thickness,0,prefix+"_right",_x+ self.mm2u(layout['right_pos'][0]+thickness),_y+ self.mm2u(layout['right_pos'][1]+height-thickness),bg,fg,width,depth,height,backlash,stack=True)

        height = height - layeroffset
        self.box_layer(layout,prefix, _x, _y, bg, fg, width, depth,height-thickness, tab_size, thickness, backlash,segment_offset)

        for horizontal_offset in segment_offset['H']:
            #inkex.debug("xpos:%s - horizontal_offset:%s - "%(layout['left_pos'][0],horizontal_offset))
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_left",_x+ self.mm2u(layout['left_pos'][0]+horizontal_offset-0.5*thickness),_y+ self.mm2u(layout['left_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_right",_x+ self.mm2u(layout['right_pos'][0]+depth-horizontal_offset-0.5*thickness),_y+ self.mm2u(layout['right_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)
        for vertical_offset in segment_offset['V']:
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_front",_x+ self.mm2u(layout['front_pos'][0]+vertical_offset+0.5*thickness),_y+ self.mm2u(layout['front_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)
            self.holes(height-thickness,tab_size,thickness,1,prefix+"_back",_x+ self.mm2u(layout['back_pos'][0]+width-vertical_offset+0.5*thickness),_y+ self.mm2u(layout['back_pos'][1]+layeroffset),bg,fg,width,depth,height,backlash)

#------------------------------------------------------------------#
# Specific shapes
#------------------------------------------------------------------#
    def box_layer(self,layout,prefix, _x, _y, bg, fg, width, depth, height, tab_size, thickness, backlash,segment_offset):
        ### Draw internal layer shapes : tabbed holes,intern part, matching rectangles

        #For each horizontal piece -> draw layer shape and tabbed hole line
        for i,horizontal_offset in enumerate(segment_offset['H']):

            self.add(self._layer(width,height,tab_size,thickness,backlash),'%s_Horizontal_layer_%s' % (prefix,i),
                    _x + self.mm2u(layout['H_layer_pos'][0]),
                    _y + self.mm2u(layout['H_layer_pos'][1]+i*height+thickness*(i!=0)), bg,fg)
            #for each perpendicular piece -> draw matching rectangle
            for offset in segment_offset['V']:
                self.add([[0,0],[thickness,0],[0,(height)/2],[-thickness,0]],'%s_Horizontal_offset_rect' % prefix,
                        _x + self.mm2u(layout['H_layer_pos'][0]+offset-thickness/2-2*thickness),
                        _y + self.mm2u(layout['H_layer_pos'][1]+i*height+thickness*(i!=0)), bg,fg)

        for i,vertical_offset in enumerate(segment_offset['V']):

            self.add(self._layer(depth,height,tab_size,thickness,backlash),'%s_Vertical_layer_%s' % (prefix,i),
                     _x + self.mm2u(layout['V_layer_pos'][0]),
                     _y + self.mm2u(layout['V_layer_pos'][1]+i*height+thickness*(i!=0)), bg, fg)
            for offset in segment_offset['H']:
                self.add([[0,0],[thickness,0],[0,(height)/2],[-thickness,0]],'%s_Vertical_offset_rect_%s' % (prefix,i),
                         _x + self.mm2u(layout['V_layer_pos'][0]+offset-thickness/2-2*thickness),
                         _y + self.mm2u(layout['V_layer_pos'][1]+i*height+thickness*(i!=0)+height/2), bg,fg)

    def lid(self,prefix,_x,_y,layout,width,depth,thickness,bg,fg):
        self.add([[0,0],[width-2*thickness,0],[0,depth-2*thickness],[-width+2*thickness,0]],'%s_top_lid' % prefix,_x + self.mm2u(layout['top_pos'][0]+width+thickness),_y + self.mm2u(layout['top_pos'][1]), bg,fg)
        self.add([[0,0],[width,0],[0,depth],[-width,0]],'%s_top_lid' % prefix,_x + self.mm2u(layout['top_pos'][0]+2*(width+thickness)),_y + self.mm2u(layout['top_pos'][1]), bg,fg)
        

    def _layer(self,width, height, tab_width, thickness, backlash):
        points = [[thickness, 0], [width - (4 * thickness), 0]]
        points.extend(self.tabs(height, tab_width, thickness, direction=1, backlash=backlash, firstUp=True,lastUp=True, inverted=True))
        points.extend([[-width + (2 * thickness), 0], []])
        points.extend(self.tabs(height, tab_width, thickness, direction=3, backlash=backlash, firstUp=True,lastUp=True, inverted=True))
        return points


