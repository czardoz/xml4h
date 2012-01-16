from xml4h.impls.interface import _XmlImplWrapper
from xml4h import nodes

import xml.dom


class XmlDomImplWrapper(_XmlImplWrapper):

    @classmethod
    def new_impl_document(self, root_tagname, ns_uri=None,
            impl_name=None, impl_features=None):
        # Create DOM implementation factory
        if impl_features is None:
            impl_features = []
        factory = xml.dom.getDOMImplementation(impl_name, impl_features)
        # Create Document from factory
        doctype = None  # TODO
        doc = factory.createDocument(ns_uri, root_tagname, doctype)
        return doc

    def wrap_impl_node(self, impl_node):
        if isinstance(impl_node, tuple):
            return nodes.Attribute(impl_node, self)
        try:
            impl_class = {
                xml.dom.Node.ELEMENT_NODE: nodes.Element,
                xml.dom.Node.ATTRIBUTE_NODE: nodes.Attribute,
                xml.dom.Node.TEXT_NODE: nodes.Text,
                xml.dom.Node.CDATA_SECTION_NODE: nodes.CDATA,
                xml.dom.Node.ENTITY_NODE: nodes.Entity,
                xml.dom.Node.PROCESSING_INSTRUCTION_NODE:
                    nodes.ProcessingInstruction,
                xml.dom.Node.COMMENT_NODE: nodes.Comment,
                # TODO
                #xml.dom.Node.DOCUMENT_NODE: ,
                #xml.dom.Node.DOCUMENT_TYPE_NODE: ,
                #xml.dom.Node.NOTATION_NODE: ,
                }[impl_node.nodeType]
            return impl_class(impl_node, self)
        except KeyError, e:
            raise NotImplementedError(
                'Wrapping of %s implementation nodes is not implemented'
                % impl_node)

    def map_node_type(self, node):
        try:
            return {
                xml.dom.Node.ELEMENT_NODE: nodes.ELEMENT,
                xml.dom.Node.ATTRIBUTE_NODE: nodes.ATTRIBUTE,
                xml.dom.Node.TEXT_NODE: nodes.TEXT,
                xml.dom.Node.CDATA_SECTION_NODE: nodes.CDATA,
                xml.dom.Node.ENTITY_NODE: nodes.ENTITY,
                xml.dom.Node.PROCESSING_INSTRUCTION_NODE:
                    nodes.PROCESSING_INSTRUCTION,
                xml.dom.Node.COMMENT_NODE: nodes.COMMENT,
                xml.dom.Node.DOCUMENT_NODE: nodes.DOCUMENT,
                xml.dom.Node.DOCUMENT_TYPE_NODE: nodes.DOCUMENT_TYPE,
                xml.dom.Node.NOTATION_NODE: nodes.NOTATION,
                }[node.nodeType]
        except KeyError, e:
            raise Exception('Unknown implementation node type: %s'
                % node.nodeType)

    def new_impl_element(self, tagname, ns_uri=None):
        if ns_uri is None:
            return self.impl_document.createElement(tagname)
        else:
            return self.impl_document.createElementNS(ns_uri, tagname)

    def new_impl_text(self, text):
        return self.impl_document.createTextNode(text)

    def new_impl_comment(self, text):
        return self.impl_document.createComment(text)

    def new_impl_instruction(self, target, data):
        return self.impl_document.createProcessingInstruction(target, data)

    def new_impl_cdata(self, text):
        return self.impl_document.createCDATASection(text)

    def find_node_elements(self, node, name='*', ns_uri='*'):
        return node.getElementsByTagNameNS(ns_uri, name)

    def get_node_namespace_uri(self, node):
        return node.namespaceURI

    def get_node_parent(self, element):
        return element.parentNode

    def get_node_children(self, element, ns_uri=None):
        return element.childNodes

    def get_node_name(self, node):
        # Attribute "node" is actually a tuple
        if isinstance(node, tuple):
            return node[0]
        else:
            return node.nodeName

    def get_node_value(self, node):
        # Attribute "node" is actually a tuple
        if isinstance(node, tuple):
            return node[1]
        else:
            return node.nodeValue

    def get_node_attributes(self, element, ns_uri=None):
        return element.attributes.items()

    def set_node_attribute(self, element, name, value, ns_uri=None):
        if ns_uri is not None:
            element.setAttributeNS(ns_uri, name, value)
        else:
            element.setAttribute(name, value)

    def add_node_child(self, parent, child, before_sibling=None):
        if before_sibling is not None:
            parent.insertBefore(child, before_sibling)
        else:
            parent.appendChild(child)

    def remove_node_child(self, parent, child, destroy_node=True):
        parent.removeChild(child)
        if destroy_node:
            child.unlink()
