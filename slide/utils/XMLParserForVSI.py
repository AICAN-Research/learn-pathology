import os.path
from xml.dom.minidom import parse, Node

import untangle
import xmltodict
import xml.etree.ElementTree as ET
from pathlib import Path
import os


class XMLParserForVSI(object):

    _document = None

    def __init__(self, slide):

        self.slide_folder = os.path.dirname(slide.path)
        self.path_to_metadata = os.path.join(self.slide_folder, 'metadata.xml')

        if os.path.exists(self.path_to_metadata):
            self.initialize_using_xmltodict()
            #self.find_elements_with_ID(id='2030')
            self.parse_xml_file()
        else:
            print(f"No metadata was found for slide with ID {slide.id}.")
            return

    def get_scale_factor(self):
        tree = ET.parse(Path(self.path_to_metadata))
        root = tree.getroot()

        property_elem = root.find(".//Property[@ID='20007']")
        cdvec2_elem = property_elem.find('CdVec2')
        values = [float(d.text) for d in cdvec2_elem.findall('double')]
        return values[0]



    # ================================
    #   xmltodict (3rd party lib)
    # ================================
    def initialize_using_xmltodict(self):
        with open(self.path_to_metadata, 'rb') as file:
            self.xmldict = xmltodict.parse(file)

        print(':)')

    def find_elements_with_attr(self, attr):
        attr = '@' + attr

    def find_elements_with_ID(self, id, trail='', parent=None):
        if parent is None:
            parent = self.xmldict

        attr = '@ID'
        trail += '-->' + parent['PropertySet']
        if hasattr(parent, attr):
            trail += attr + parent[attr]

        if attr in parent.keys():
            if parent[attr] == id:
                if hasattr(parent[attr], 'Property'):
                    return parent[attr]['Property'], trail
                elif hasattr(parent[attr], 'Component'):
                    return parent[attr]['Component'], trail
                else:
                    return f'Found attribute {attr} in node'
        else:   # search children
            for child in parent['Property']:
                self.find_elements_with_ID(id, trail, child)

    def parse_xml_file(self):
        # Slide info
        try:
            slide_info = self.xmldict['PropertySet']['Property'][1]['PropertySet']['Property'][0]['PropertySet']['Property']
        except Exception as exc:
            slide_info = self.xmldict['PropertySet']['Property'][1]['PropertySet']['Property'][1]['PropertySet']['Property']
        for property in slide_info:
            print('{ ', end='')
            for k, v in property.items():
                print(k, ': ', v, ', ', sep='', end='')
            print(' }')

        #   --> {'@ID': '2030', 'PName': 'ImageLayerName', 'CString': '20x FocusMap'}

        # Get objective image magnification
        # self.xmldict['PropertySet']['Property'][0]['Component'][3]['PropertySet']['Property'][3]['PropertySet']['Property'][1]['PropertySet']['Property'][2]
        #   --> {'@ID': '2030', 'PName': 'ImageLayerName', 'CString': '20x FocusMap'}
        # self.xmldict['PropertySet']['Property'][0]['Component'][2]['PropertySet']['Property'][3]['PropertySet']['Property'][1]['PropertySet']['Property'][1]
        #   -->  {'@ID': '2030', 'PName': 'ImageLayerName', 'CString': 'EFI 20x'}

        self._data = {}


        print(':)')

    # ================================
    #   untangle (3rd party lib)
    # ================================
    def initialize_using_untangle(self):
        self.xml_untangle_root = untangle.parse(self.path_to_metadata)
        print(':)')

    def get_xml_node(self, id=None, attr=None):
        if id is not None:
            self.xml_untangle_root[str(id)]
        else: # id not specified
            if attr is None:
                raise ValueError("XML Node ID or attribute name must specified.")
            else: # only attr is specified
                self.xml_untangle_root[str(attr)]

    # ================================
    #   xml.dom.minidom
    # ================================
    def initialize_using_xml_minidom(self):
        self.create_DOM_tree()
        self.set_id_attribute(self._document)
        self.remove_whitespace(self._document)

    def create_DOM_tree(self):
        # Creates a DOM tree
        document = parse(self.path_to_metadata)
        self._document = document

    def set_id_attribute(self, parent, attribute_name='id'):
        if parent.nodeType == Node.ELEMENT_NODE:
            parent.setIdAttribute(attribute_name)
        for child in parent.childNodes:
            self.set_id_attribute(child, attribute_name)

    def remove_whitespace(self, node):
        if node.nodeType == Node.TEXT_NODE:
            if node.nodeValue.strip() == "":
                node.nodeValue = ""
        for child in node.childNodes:
            self.remove_whitespace(child)
