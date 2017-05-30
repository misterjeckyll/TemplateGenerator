# encoding: utf-8
import math
import inkex
import simplestyle
#------------------------------------------------------------------#
# Exception
#------------------------------------------------------------------#
class BoxGenrationError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class BoxEffect():
# ------------------------------------------------------------------#
# Format and utility functions
# ------------------------------------------------------------------#
    def add(self,vectorlist,id,x_pos,y_pos):
        ### Add the svg representation of a list of vectors to the main list of shapes
        self.list_of_paths.append(self.getPath(self.toPathString(self.mm2u(vectorlist)),self.prefix+'_'+id,x_pos,y_pos,self.fg,self.bg))
        
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

    def getPath(self, path, path_id, _x, _y,fg,bg):
        style = {'stroke': fg,
                 'fill': bg if(bg) else 'none',
                 'stroke-width': 0.1}
        return {
            'style': simplestyle.formatStyle(style),
            'id': path_id,
            'transform': "translate(%s,%s)" % (_x, _y),
            'd': path
        }
    def _tab_calc(self,length,tab_width,thickness,restrictive=False):

        ### Calcultate tab size and number
        nb_tabs = math.floor(length / tab_width)
        nb_tabs = int(nb_tabs - 1 + (nb_tabs % 2))
        tab_real_width = length / nb_tabs
        #inkex.debug("Pour une largeur de %s et des encoches de %s => Nombre d'encoches : %s Largeur d'encoche : %s" % (length, tab_width, nb_tabs, tab_real_width))

        if restrictive:
            ### Check if no inconsistency on tab size and number
            if (tab_real_width <= thickness * 1.5):
                raise BoxGenrationError("Attention les encoches resultantes (%s mm) ne sont pas assez larges au vue de l'épaisseur de votre materiaux. Merci d'utiliser une taille d'encoches coherente avec votre boite" % tab_real_width)
            elif (nb_tabs < 1 ):
                raise BoxGenrationError("Attention vous n'aurez aucune encoche sur cette longueur, c'est une mauvaise idée !!! Indiquez une taille d'encoche correcte pour votre taille de boite")
        else:
            ### Assume default values
            if(tab_real_width < thickness * 1.5):
                nb_tabs = math.floor(length / (thickness*1.5))
                nb_tabs = int(nb_tabs - 1 + (nb_tabs % 2))
                tab_real_width = length / nb_tabs
        return (tab_real_width,nb_tabs)

# ------------------------------------------------------------------#
# Tabbed Holes
# ------------------------------------------------------------------#
    def holes(self,length ,direction,id,_x,_y,tab_width, thickness, backlash,inverted = True):
        '''
            * Génere une suite de trou pour des encoches d'environ 
            * <tab_width>, sur un longueur de <length>,
            * pour un materiau d'epaisseur <thickness>.
            *
            * options :
            *   - direction : 0 ligne horizontale de gauche à droite, 1 ligne verticale de haut en bas
            *   - inverted : True pour des trous d'encoches impair, False pour des trous d'encoches pair
        '''
        tab_real_width,nbtabs = self._tab_calc(length,tab_width,thickness)
        hrect = [[backlash, 0],[0,thickness],[tab_real_width+backlash,0],[0,-thickness]]

        if(not direction):
            for i in range(1,nbtabs+1):
                if (i % 2 == inverted):
                    self.add(hrect,'%s_Horizontal_Hole'%id,_x + self.mm2u((i-inverted) * tab_real_width-0.5*backlash*(i==0)),_y)
        else:
            for i in range(1,nbtabs+1):
                if (i % 2 == 0):
                    self.add(self._rotate_path(hrect,1),'%s_Vertical_Hole'%id ,_x , _y+ self.mm2u((i-inverted)*tab_real_width-0.5*backlash*(i==0)))

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
        tab_real_width,nbtabs = self._tab_calc(length,tab_width,thickness)
        return self._rotate_path(self._generate_tabs_path(tab_real_width, nbtabs, thickness, direction=direction, **args), direction)

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
# Path of each box part (usable as standalones)
# ------------------------------------------------------------------#
### Intern layer shape
    def _layer(self,width, height, tab_width, thickness, backlash):
        points = [[thickness, 0], [width - (4 * thickness), 0]]
        points.extend(self.tabs(height, tab_width, thickness, direction=1, backlash=backlash, firstUp=True,lastUp=True, inverted=True))
        points.extend([[-width + (2 * thickness), 0], []])
        points.extend(self.tabs(height, tab_width, thickness, direction=3, backlash=backlash, firstUp=True,lastUp=True, inverted=True))
        return points

### Bottom/top shapes

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

### Front shapes

    def _front_without_top(self, width, height, tab_width, thickness, backlash):
        # print("front_without_top")
        points = [[0, 0], [width, 0]]
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True))
        points.extend(self.tabs(width,tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True))
        return points

    def _front_with_top(self, width, height, tab_width, thickness, backlash):
        # print("front_with_top")
        points = [[0, thickness]]
        points.extend(self.tabs(width, tab_width, thickness,direction=0, backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(height - (thickness * 2), tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True))
        points.extend(self.tabs(width, tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(height - (thickness * 2), tab_width, thickness, direction=3,backlash=backlash,firstUp=True,lastUp=True))
        return points

    def _stackable_front_without_top(self, width, height, tab_width, thickness, backlash):
        stackheight=thickness
        stackoffset=width/10
        points = [[0, 0], [stackoffset, 0],[stackoffset,-stackheight],[width-4*stackoffset,0],[stackoffset,stackheight],[stackoffset,0]]
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True))
        points.extend([[0,2*thickness+stackheight],[-stackoffset,0],[-stackoffset,-stackheight],[-width +4*stackoffset, 0],[-stackoffset,stackheight],[-stackoffset,0],[0,-stackheight-2*thickness]])
        points.extend(self.tabs(height-thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True))
        return points

### Side shapes

    def _side_without_top(self, depth, height, tab_width, thickness, backlash):
        # print("side_without_top")
        points = [[thickness, 0], [depth - (4 * thickness), 0]]
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(depth, tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True,cutOff=True))
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        return points

    def _side_with_top(self, depth, height, tab_width, thickness, backlash):
        # print("side_with_top")
        points = [[thickness, thickness]]
        points.extend(self.tabs(depth, tab_width, thickness,direction=0,backlash=backlash,firstUp=True,lastUp=True,inverted=True,cutOff=True))
        points.extend(self.tabs(height - (2 * thickness), tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend(self.tabs(depth, tab_width, thickness,direction=2,backlash=backlash,firstUp=True,lastUp=True,inverted=True,cutOff=True))
        points.extend(self.tabs(height - (2 * thickness), tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        return points

    def _stackable_side_without_top(self, depth, height, tab_width, thickness, backlash):
        # print("side_without_top")
        stackheight=thickness
        stackoffset=depth/10
        points = [[stackoffset, 0],[stackoffset,-stackheight],[depth-4*stackoffset-2*thickness,0],[stackoffset,stackheight],[stackoffset,0]]
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=1,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        points.extend([[0,2*thickness+stackheight],[-stackoffset,0],[-stackoffset,-stackheight],[-depth + (2 * thickness)+4*stackoffset, 0],[-stackoffset,stackheight],[-stackoffset,0],[0,-stackheight-2*thickness]])
        points.extend(self.tabs(height - thickness, tab_width, thickness,direction=3,backlash=backlash,firstUp=True,lastUp=True,inverted=True))
        return points

#------------------------------------------------------------------#
# Main Shapes of different types of box
#------------------------------------------------------------------#

    def box_with_top(self,prefix, _x, _y,fg,bg, width, depth, height, tab_width, thickness, backlash):
        paths = []
        paths.append(self.getPath(self.toPathString(self.mm2u(self._bottom(width, depth, tab_width, thickness, backlash))),'%s_bottom'% prefix,_x,_y,bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._bottom(width, depth, tab_width, thickness, backlash))),'%s_top' % prefix, _x + self.mm2u(2 * thickness + width), _y + self.mm2u(1 * thickness),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._front_with_top(width, height, tab_width, thickness, backlash))),'%s_front'% prefix , _x + self.mm2u(2 * thickness + width), _y + self.mm2u(2 * thickness + depth),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._front_with_top(width, height, tab_width, thickness, backlash))),'%s_back'% prefix , _x + self.mm2u(1 * thickness), _y + self.mm2u(2 * thickness + depth),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._side_with_top(depth, height, tab_width, thickness, backlash))),'%s_left'% prefix , _x + self.mm2u(2 * thickness + depth), _y + self.mm2u(3 * thickness + depth + height),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._side_with_top(depth, height, tab_width, thickness, backlash))),'%s_right' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(3 * thickness + depth + height),bg,fg))
        return paths

    def box_without_top(self,prefix, _x, _y,fg,bg, width, depth, height, tab_width, thickness, backlash):
        paths = []
        paths.append(self.getPath(self.toPathString(self.mm2u(self._bottom(width, depth, tab_width, thickness, backlash))),'%s_bottom'% prefix , _x + self.mm2u(1 * thickness), _y + self.mm2u(1 * thickness),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._front_without_top(width, height, tab_width, thickness, backlash))),'%s_front' % prefix, _x + self.mm2u(2 * thickness + width), _y + self.mm2u(2 * thickness + depth),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._front_without_top(width, height, tab_width, thickness, backlash))),'%s_back'% prefix , _x + self.mm2u(1 * thickness), _y + self.mm2u(2 * thickness + depth),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._side_without_top(depth, height, tab_width, thickness, backlash))),'%s_left'% prefix , _x + self.mm2u(2 * thickness + depth), _y + self.mm2u(3 * thickness + depth + height),bg,fg))
        paths.append(self.getPath(self.toPathString(self.mm2u(self._side_without_top(depth, height, tab_width, thickness, backlash))),'%s_right' % prefix, _x + self.mm2u(1 * thickness), _y + self.mm2u(3 * thickness + depth + height),bg,fg))
        return paths

    def box_without_top_selection(self, _x, _y,segment_offset,layeroffset,lid):
        """ 
            * Draw a Box with internal parts or not
            *
            * :params segment_offset:
            * dictionnary of the offset(float) to the box of each internal segment
            * {
            *   'H':[y_offset_horizontal_segment1, y_offset_horizontal_segment2,...],
            *   'V':[x_offset_vertical_segment1,...]
            * }
        """
        ### For convenient use
        width, depth, height,tab_width, thickness, backlash = self.boxparams
        params = (tab_width, thickness, backlash)
        layout = self.layout

        ### Basic lid
        if(lid):
            layeroffset=thickness if layeroffset<thickness else layeroffset
            self.lid(_x,_y,width,depth,thickness)

        ### Draw each sides of the box
        self.add(self._bottom(width,depth,*params),'bottom' ,_x + self.mm2u(layout['bottom'][0]),_y + self.mm2u(layout['bottom'][1]))
        self.add(self._front_without_top(width,height,*params),'front' ,_x + self.mm2u(layout['front'][0]),_y + self.mm2u(layout['front'][1]))
        self.add(self._front_without_top(width,height,*params),'back' ,_x + self.mm2u(layout['back'][0]),_y + self.mm2u(layout['back'][1]))
        self.add(self._side_without_top(depth,height,*params),'left' ,_x + self.mm2u(layout['left'][0]),_y + self.mm2u(layout['left'][1]))
        self.add(self._side_without_top(depth,height,*params),'right' ,_x + self.mm2u(layout['right'][0]),_y + self.mm2u(layout['right'][1]))

        ### Draw each internal layers
        height = height - layeroffset
        self.box_layer( _x, _y, width, depth,height-thickness,layeroffset,segment_offset, *params)
        for horizontal_offset in segment_offset['H']:
            #inkex.debug("xpos:%s - horizontal_offset:%s - "%(layout['left'][0],horizontal_offset))
            self.holes(height-thickness,1,"left",_x+ self.mm2u(layout['left'][0]+horizontal_offset-1.5*thickness),_y+ self.mm2u(layout['left'][1]+layeroffset),*params)
            self.holes(height-thickness,1,"right",_x+ self.mm2u(layout['right'][0]+depth-horizontal_offset-1.5*thickness),_y+ self.mm2u(layout['right'][1]+layeroffset),*params)
        for vertical_offset in segment_offset['V']:
            self.holes(height-thickness,1,"front",_x+ self.mm2u(layout['front'][0]+vertical_offset+0.5*thickness),_y+ self.mm2u(layout['front'][1]+layeroffset),*params)
            self.holes(height-thickness,1,"back",_x+ self.mm2u(layout['back'][0]+width-vertical_offset+0.5*thickness),_y+ self.mm2u(layout['back'][1]+layeroffset),*params)

    def box_with_top_selection(self, _x, _y,segment_offset,layeroffset):
        ### params rename for convenient use
        layout = self.layout
        width, depth, height,tab_width, thickness, backlash = self.boxparams
        params = (tab_width, thickness, backlash)

        ### Draw each sides of the box
        self.add(self._bottom(width,depth,*params),'bottom' ,_x + self.mm2u(layout['bottom'][0]),_y + self.mm2u(layout['bottom'][1]))
        self.add(self._bottom(width,depth,*params),'top' ,_x + self.mm2u(layout['top'][0]),_y + self.mm2u(layout['top'][1]))
        self.add(self._front_with_top(width,height,*params),'front' ,_x + self.mm2u(layout['front'][0]),_y + self.mm2u(layout['front'][1]))
        self.add(self._front_with_top(width,height,*params),'back' ,_x + self.mm2u(layout['back'][0]),_y + self.mm2u(layout['back'][1]))
        self.add(self._side_with_top(depth,height,*params),'left' ,_x + self.mm2u(layout['left'][0]),_y + self.mm2u(layout['left'][1]))
        self.add(self._side_with_top(depth,height,*params),'right' ,_x + self.mm2u(layout['right'][0]),_y + self.mm2u(layout['right'][1]))
        
        height = height - layeroffset
        self.box_layer( _x, _y, width, depth,height-2*thickness,layeroffset,segment_offset,*params)
        for horizontal_offset in segment_offset['H']:
            #inkex.debug("xpos:%s - horizontal_offset:%s - "%(layout['left'][0],horizontal_offset))
            self.holes(height-2*thickness,1,"left",_x+ self.mm2u(layout['left'][0]+horizontal_offset+0.5*thickness),_y+ self.mm2u(layout['left'][1]+layeroffset+thickness),*params)
            self.holes(height-2*thickness,1,"right",_x+ self.mm2u(layout['right'][0]+depth-horizontal_offset+0.5*thickness),_y+ self.mm2u(layout['right'][1]+layeroffset+thickness),*params)
        for vertical_offset in segment_offset['V']:
            self.holes(height-2*thickness,1,"front",_x+ self.mm2u(layout['front'][0]+vertical_offset+0.5*thickness),_y+ self.mm2u(layout['front'][1]+layeroffset+thickness),*params)
            self.holes(height-2*thickness,1,"back",_x+ self.mm2u(layout['back'][0]+width-vertical_offset+0.5*thickness),_y+ self.mm2u(layout['back'][1]+layeroffset+thickness),*params)

    def box_without_top_stackable_selection(self, _x, _y,segment_offset,layeroffset,lid):

        ### For convenient use
        width, depth, height,tab_width, thickness, backlash = self.boxparams
        params = (tab_width, thickness, backlash)
        layout = self.layout
        
        ### Adjust layout positions because stackable parts are bigger
        layout['left'][1] += 3*thickness
        layout['right'][1] += 3*thickness
        layout['Hlayer'][1] += 5 * thickness
        layout['Vlayer'][1] += 5 * thickness

        ### Basic lid
        if(lid):
            layeroffset=thickness if layeroffset<thickness else layeroffset
            self.lid(_x,_y,width,depth,thickness)

        ### Draw each sides of the box
        self.add(self._stackable_bottom(width,depth,*params),'bottom',_x + self.mm2u(layout['bottom'][0]),_y + self.mm2u(layout['bottom'][1]))
        self.add(self._stackable_front_without_top(width,height,*params), 'front',_x + self.mm2u(layout['front'][0]),_y + self.mm2u(layout['front'][1]))
        self.add(self._stackable_front_without_top(width,height,*params), 'back',_x + self.mm2u(layout['back'][0]),_y + self.mm2u(layout['back'][1]))
        self.add(self._stackable_side_without_top(depth,height,*params), 'left',_x + self.mm2u(layout['left'][0]),_y + self.mm2u(layout['left'][1]))
        self.add(self._stackable_side_without_top(depth,height,*params), 'right',_x + self.mm2u(layout['right'][0]),_y + self.mm2u(layout['right'][1]))

        ### Draw the coresponding lines of finger holes
        self.holes(width-(4*thickness),0,'front',_x+ self.mm2u(layout['front'][0]+2*thickness),_y+ self.mm2u(layout['front'][1]+height-thickness),*params)
        self.holes(width-(4*thickness),0,'back',_x+ self.mm2u(layout['back'][0]+2*thickness),_y+ self.mm2u(layout['back'][1]+height-thickness),*params)
        self.holes(depth-(4*thickness),0,'left',_x+ self.mm2u(layout['left'][0]+thickness),_y+ self.mm2u(layout['left'][1]+height-thickness),*params)
        self.holes(depth-(4*thickness),0,'right',_x+ self.mm2u(layout['right'][0]+thickness),_y+ self.mm2u(layout['right'][1]+height-thickness),*params)

        ### Intern Layer parts
        height = height - layeroffset
        self.box_layer( _x, _y, width, depth,height-thickness,layeroffset,segment_offset,*params)

        for horizontal_offset in segment_offset['H']:
            #inkex.debug("xpos:%s - horizontal_offset:%s - "%(layout['left'][0],horizontal_offset))
            self.holes(height-thickness,1,"left",_x+ self.mm2u(layout['left'][0]+horizontal_offset-0.5*thickness),_y+ self.mm2u(layout['left'][1]+layeroffset),*params)
            self.holes(height-thickness,1,"right",_x+ self.mm2u(layout['right'][0]+depth-horizontal_offset-0.5*thickness),_y+ self.mm2u(layout['right'][1]+layeroffset),*params)
        for vertical_offset in segment_offset['V']:
            self.holes(height-thickness,1,"front",_x+ self.mm2u(layout['front'][0]+vertical_offset+0.5*thickness),_y+ self.mm2u(layout['front'][1]+layeroffset),*params)
            self.holes(height-thickness,1,"back",_x+ self.mm2u(layout['back'][0]+width-vertical_offset+0.5*thickness),_y+ self.mm2u(layout['back'][1]+layeroffset),*params)

#------------------------------------------------------------------#
# Specific shapes
#------------------------------------------------------------------#
    def box_layer(self, _x, _y, width, depth, height,layeroffset,segment_offset, tab_width, thickness,backlash):
        layout = self.layout
        params = (tab_width,thickness,backlash)
        ### Draw internal layer shapes : tabbed holes,intern part, matching rectangles
        rect = [[0,0],[thickness,0],[0,(height)/2],[-thickness,0]]
        #For each horizontal piece -> draw layer shape and tabbed hole line
        for i,horizontal_offset in enumerate(segment_offset['H']):
            self.add(self._layer(width,height,*params),'Horizontal_layer_%s' % (i),_x + self.mm2u(layout['Hlayer'][0]),_y + self.mm2u(layout['Hlayer'][1]+i*height+thickness*(i!=0)))
            for offset in segment_offset['V']:#for each perpendicular piece -> draw matching rectangle
                self.add(rect,'Horizontal_rect' ,_x + self.mm2u(layout['Hlayer'][0]+offset-thickness/2-2*thickness),_y + self.mm2u(layout['Hlayer'][1]+i*height+thickness*(i!=0)))
        for i,vertical_offset in enumerate(segment_offset['V']):
            self.add(self._layer(depth,height,*params),'Vertical_layer_%s' % (i),_x + self.mm2u(layout['Vlayer'][0]),_y + self.mm2u(layout['Vlayer'][1]+i*height+thickness*(i!=0)))
            for offset in segment_offset['H']:
                self.add(rect,'Vertical_rect_%s' % (i),_x + self.mm2u(layout['Vlayer'][0]+offset-thickness/2-2*thickness),_y + self.mm2u(layout['Vlayer'][1]+i*height+thickness*(i!=0)+height/2))

    def lid(self,_x,_y,width,depth,thickness):
        layout = self.layout
        self.add([[0,0],[width-2*thickness,0],[0,depth-2*thickness],[-width+2*thickness,0]],'top_lid' ,_x + self.mm2u(layout['top'][0]+width+.3),_y + self.mm2u(layout['top'][1]))
        self.add([[0,0],[width,0],[0,depth],[-width,0]],'top_lid' ,_x + self.mm2u(layout['top'][0]+2*(width+.3)),_y + self.mm2u(layout['top'][1]))