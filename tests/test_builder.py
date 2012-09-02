# -*- coding: utf-8 name> -*-
import unittest
from StringIO import StringIO
import functools

from xml4h import builder, nodes, impl_preferred
from xml4h.impls.lxml_etree import LXMLAdapter


class TestBuilderMethods(unittest.TestCase):

    def test_create_minidom(self):
        import xml.dom
        from xml4h.impls.xml_dom_minidom import XmlDomImplAdapter
        xmlb = builder('DocRoot', adapter=XmlDomImplAdapter)
        self.assertIsInstance(
            xmlb.anchor_element.impl_document, xml.dom.minidom.Document)


class BaseBuilderNodesTest(object):

    @property
    def my_builder(self):
        raise NotImplementedError()

    def test_element(self):
        xmlb = self.my_builder('DocRoot')
        # Aliases
        self.assertEqual(xmlb.element, xmlb.elem)
        self.assertEqual(xmlb.element, xmlb.e)
        # Add elements
        xmlb = (
            self.my_builder('DocRoot')
                .e('Deeper')
                .e('AndDeeper')
                .e('DeeperStill'))
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <Deeper>\n'
            '        <AndDeeper>\n'
            '            <DeeperStill/>\n'
            '        </AndDeeper>\n'
            '    </Deeper>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())

    def test_root(self):
        xmlb = (
            self.my_builder('DocRoot')
                .e('Deeper')
                .e('AndDeeper')
                .e('DeeperStill'))
        # Builder node is at DeeperStill element, but we can get to the root
        self.assertEqual('DeeperStill', xmlb.anchor_element.name)
        self.assertEqual('DocRoot', xmlb.anchor_element.root.name)

    def test_up(self):
        xmlb = (
            self.my_builder('DocRoot')
                .e('Deeper')
                .e('AndDeeper')
                .e('DeeperStill'))
        self.assertEqual('DeeperStill', xmlb.anchor_element.name)

        # Can navigate up XML DOM tree one step at a time...
        self.assertEqual('AndDeeper', xmlb.up().anchor_element.name)
        self.assertEqual('Deeper', xmlb.up().up().anchor_element.name)
        self.assertEqual('DocRoot', xmlb.up().up().up().anchor_element.name)
        # ...but not past the root element
        self.assertEqual('DocRoot',
            xmlb.up().up().up().up().anchor_element.name)

        # Can navigate up by count...
        self.assertEqual('AndDeeper', xmlb.up().anchor_element.name)
        self.assertEqual('Deeper', xmlb.up(2).anchor_element.name)
        self.assertEqual('DocRoot', xmlb.up(3).anchor_element.name)
        # ...but not past the root element
        self.assertEqual('DocRoot', xmlb.up(100).anchor_element.name)

        # Can navigate up to a given element tagname
        self.assertEqual('AndDeeper',
            xmlb.up(to_tagname='AndDeeper').anchor_element.name)
        self.assertEqual('Deeper',
            xmlb.up(to_tagname='Deeper').anchor_element.name)
        self.assertEqual('DocRoot',
            xmlb.up(to_tagname='DocRoot').anchor_element.name)
        # ...but not past the root element if there is no such tagname
        self.assertEqual('DocRoot',
            xmlb.up(to_tagname='NoSuchName').anchor_element.name)

    def test_attributes(self):
        # Aliases
        xmlb = self.my_builder('DocRoot')
        self.assertEqual(xmlb.attributes, xmlb.attrs)
        self.assertEqual(xmlb.attributes, xmlb.a)
        # Add attributes
        xmlb = (
            self.my_builder('DocRoot')
              .e('Elem1').attrs(x=1).up()  # Add a single name/value pair
              .e('Elem2').attrs(a='a', b='bee').up()  # Add multiple
              .e('Elem3').attrs([  # Add list of tuple pairs
                  ('hyphenated-name', 'v2'),
                  ]).up()
              .e('Elem4').attrs({  # Add a dictionary
                  'twelve': 3 * 4,
                  }).up()
              # Attributes given in first arg trump same name in kwargs
              .e('Elem5').attrs(
                  {'test': 'value-in-first-arg'},
                  test='value-in-kwargs').up()
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <Elem1 x="1"/>\n'
            '    <Elem2 a="a" b="bee"/>\n'
            '    <Elem3 hyphenated-name="v2"/>\n'
            '    <Elem4 twelve="12"/>\n'
            '    <Elem5 test="value-in-first-arg"/>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())

    def test_xml(self):
        xmlb = (
            self.my_builder('DocRoot')
                .e('Elem1').up()
                .e('Elem2')
                    .e('Elem3').up())
        # xml() method outputs current node content and descendents only
        self.assertEqual(
            '<Elem2>\n    <Elem3/>\n</Elem2>',
            xmlb.anchor_element.xml())
        # Default string output is utf-8, and pretty-printed
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <Elem1/>\n'
            '    <Elem2>\n'
            '        <Elem3/>\n'
            '    </Elem2>\n'
            '</DocRoot>\n'
            )
        self.assertEqual(xml, xmlb.anchor_element.doc_xml())
        # Mix it up a bit
        self.assertEqual(
            '<DocRoot>\n'
            '    <Elem1/>\n'
            '    <Elem2>\n'
            '        <Elem3/>\n'
            '    </Elem2>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml(omit_declaration=True))
        self.assertEqual(
            '<?xml version="1.0" encoding="latin1"?>\n'
            '<DocRoot>\n'
            '  <Elem1/>\n'
            '  <Elem2>\n'
            '    <Elem3/>\n'
            '  </Elem2>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml(encoding='latin1', indent=2))
        self.assertEqual(
            '<?xml version="1.0"?>\t'
            '<DocRoot>\t'
            '        <Elem1/>\t'
            '        <Elem2>\t'
            '                <Elem3/>\t'
            '        </Elem2>\t'
            '</DocRoot>\t',
            xmlb.anchor_element.doc_xml(encoding=None, indent=8, newline='\t'))

    def test_write(self):
        xmlb = (
            self.my_builder('DocRoot')
                .e('Elem1').up()
                .e('Elem2'))
        # write() method outputs only current node and descendents
        writer = StringIO()
        xmlb.anchor_element.write(writer)
        self.assertEqual('<Elem2/>', writer.getvalue())
        # Default write output is utf-8, with no pretty-printing
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<DocRoot>'
                '<Elem1/>'
                '<Elem2/>'
            '</DocRoot>'
            )
        writer = StringIO()
        xmlb.anchor_element.doc_write(writer)
        self.assertEqual(xml, writer.getvalue())
        # Mix it up a bit
        writer = StringIO()
        xmlb.anchor_element.doc_write(writer, omit_declaration=True)
        self.assertEqual(
            '<DocRoot>'
                '<Elem1/>'
                '<Elem2/>'
            '</DocRoot>',
            writer.getvalue())
        writer = StringIO()
        xmlb.anchor_element.doc_write(writer, encoding='latin1', indent=2)
        self.assertEqual(
            '<?xml version="1.0" encoding="latin1"?>'
            '<DocRoot>'
            '  <Elem1/>'
            '  <Elem2/>'
            '</DocRoot>',
            writer.getvalue())
        writer = StringIO()
        xmlb.anchor_element.doc_write(writer,
            encoding=None, indent=8, newline='\t')
        self.assertEqual(
            '<?xml version="1.0"?>\t'
            '<DocRoot>\t'
            '        <Elem1/>\t'
            '        <Elem2/>\t'
            '</DocRoot>\t',
            writer.getvalue())

    def test_text(self):
        # Aliases
        xmlb = self.my_builder('DocRoot')
        self.assertEqual(xmlb.text, xmlb.t)
        # Add text values to elements
        xmlb = (
            self.my_builder('DocRoot')
              .e('Elem1').t('A text value').up()
              .e('Elem2').t('Seven equals %s' % 7).up()
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <Elem1>A text value</Elem1>\n'
            '    <Elem2>Seven equals 7</Elem2>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())
        # Multiple text nodes, and text node next to nested element
        xmlb = (
            self.my_builder('DocRoot')
              .e('Elem1')
                .t('First text value')
                .t('Second text value').up()
              .e('Elem2')
                .t('Text')
                .e('Nested')
                .t('Text in nested').up()
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <Elem1>First text valueSecond text value</Elem1>\n'
            '    <Elem2>Text\n'
            '        <Nested>Text in nested</Nested>\n'
            '    </Elem2>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())

    def test_comment(self):
        # Aliases
        xmlb = self.my_builder('DocRoot')
        self.assertEqual(xmlb.comment, xmlb.c)
        # Add text values to elements
        xmlb = (
            self.my_builder('DocRoot')
                .e('Elem1').c('Here is my comment').up()
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <Elem1><!--Here is my comment--></Elem1>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())

    def test_instruction(self):
        # Aliases
        xmlb = self.my_builder('DocRoot')
        self.assertEqual(
            xmlb.instruction, xmlb.processing_instruction)
        self.assertEqual(xmlb.instruction, xmlb.i)
        # Add text values to elements
        xmlb = (
            self.my_builder('DocRoot').i('inst-target', 'inst-data')
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <?inst-target inst-data?>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())

    def test_namespace(self):
        # Define namespaces on elements after creation
        xmlb = (
            self.my_builder('DocRoot', ns_uri='urn:default')
                .e('Elem1', ns_uri='urn:elem1').up()
                .e('Elem2').ns_prefix('myns', 'urn:elem2').up()
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot xmlns="urn:default">\n'
            '    <Elem1 xmlns="urn:elem1"/>\n'
            '    <Elem2 xmlns:myns="urn:elem2"/>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())
        # Test namespaces work as expected when searching/traversing DOM
        self.assertEqual(1, len(xmlb.find(name='Elem1')))  # Ignore namespace
        self.assertEqual(1, len(xmlb.find(name='Elem1', ns_uri='urn:elem1')))
        self.assertEqual(1, len(xmlb.doc_find(ns_uri='urn:elem1')))
        self.assertEqual(0, len(xmlb.find(name='Elem1', ns_uri='urn:wrong')))
        self.assertEqual(['Elem1'],
            [n.name for n in xmlb.anchor_element.children_in_ns('urn:elem1')])
        self.assertEqual(['DocRoot', 'Elem2'],
            [n.name for n in xmlb.doc_find(ns_uri='urn:default')])
        self.assertEqual(['Elem2'],
            [n.name for n in xmlb.anchor_element.children_in_ns('urn:default')])
        # Set namespaces of elements and attributes on creation
        xmlb = (
            self.my_builder('DocRoot', ns_uri='urn:default')
                .ns_prefix('myns', 'urn:custom')
                # Elements in default namespace
                .e('NSDefaultImplicit').up()
                .e('NSDefaultExplicit', ns_uri='urn:default').up()
                # Elements in custom namespace
                .e('NSCustomExplicit', ns_uri='urn:custom').up()
                .e('myns:NSCustomWithPrefixImplicit').up()
                .e('myns:NSCustomWithPrefixExplicit',
                    ns_uri='urn:custom').up()
                # Attributes in namespace
                .e('Attrs1')
                    .attrs({'default-ns-implicit': 1})
                    .attrs({'default-ns-explicit': 1},
                        ns_uri='urn:default').up()
                .e('Attrs2')
                    .attrs({'myns:custom-ns-prefix-implicit': 1})
                    .attrs({'myns:custom-ns-prefix-explicit': 1},
                        ns_uri='urn:custom')
            )
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot xmlns="urn:default" xmlns:myns="urn:custom">\n'
            '    <NSDefaultImplicit/>\n'
            '    <NSDefaultExplicit xmlns="urn:default"/>\n'
            '    <%sNSCustomExplicit xmlns="urn:custom"/>\n'
            '    <myns:NSCustomWithPrefixImplicit/>\n'
            '    <myns:NSCustomWithPrefixExplicit xmlns="urn:custom"/>\n'
            '    <Attrs1 default-ns-explicit="1"'
                       ' default-ns-implicit="1"/>\n'
            '    <Attrs2'
                       ' myns:custom-ns-prefix-explicit="1"'
                       ' myns:custom-ns-prefix-implicit="1"/>\n'
            '</DocRoot>\n'
            % (self.adapter == LXMLAdapter and 'myns:' or ''))
            # TODO: lxml outputs prefix in more situations than minidom
        self.assertEqual(xml, xmlb.anchor_element.doc_xml())
        # Test namespaces work as expected when searching/traversing DOM
        self.assertEqual(
            ['DocRoot', 'NSDefaultImplicit', 'NSDefaultExplicit',
             'Attrs1', 'Attrs2'],
            [n.name for n in xmlb.doc_find(ns_uri='urn:default')])
        if self.adapter == LXMLAdapter:  # TODO: Differing prefix output
            self.assertEqual(
                ['myns:NSCustomExplicit', 'myns:NSCustomWithPrefixImplicit',
                 'myns:NSCustomWithPrefixExplicit'],
                [n.name for n in xmlb.doc_find(ns_uri='urn:custom')])
        else:
            self.assertEqual(
                ['NSCustomExplicit', 'myns:NSCustomWithPrefixImplicit',
                 'myns:NSCustomWithPrefixExplicit'],
                [n.name for n in xmlb.doc_find(ns_uri='urn:custom')])
        self.assertEqual(
            ['NSCustomExplicit', 'NSCustomWithPrefixImplicit',
             'NSCustomWithPrefixExplicit'],
            [n.local_name for n in xmlb.doc_find(ns_uri='urn:custom')])
        # Check attribute namespaces
        self.assertEqual([nodes.Node.XMLNS_URI, nodes.Node.XMLNS_URI],
            [n.namespace_uri
             for n in xmlb.anchor_element.root.attribute_nodes])
        attrs1_elem = xmlb.document.find_first('Attrs1')
        self.assertEqual([None, None],
            [n.namespace_uri for n in attrs1_elem.attribute_nodes])
        attrs2_elem = xmlb.document.find_first('Attrs2')
        self.assertEqual(['urn:custom', 'urn:custom'],
            [n.namespace_uri for n in attrs2_elem.attribute_nodes])

    def test_element_creation_with_namespace(self):
        # Define namespaces on elements using prefixes
        xmlb = (
            self.my_builder('DocRoot', ns_uri='urn:default')
                .ns_prefix('testns', 'urn:test')
                .e('testns:Elem1').up()  # Standard XML-style prefix name
                .e('{urn:test}Elem2').up()  # ElementTree-style prefix URI
                .e('Attrs').attrs({
                    'testns:attrib1': 'value1',
                    '{urn:test}attrib2': 'value2'})
            )
        root = xmlb.anchor_element.root
        self.assertEqual('testns', root.find_first(name='Elem1').prefix)
        self.assertEqual('testns', root.find_first(name='Elem2').prefix)
        self.assertEqual(
            'urn:test', root.find_first(name='Elem1').namespace_uri)
        self.assertEqual(
            'urn:test', root.find_first(name='Elem2').namespace_uri)
        self.assertEqual('testns:Elem1', root.find_first(name='Elem1').name)
        self.assertEqual('testns:Elem2', root.find_first(name='Elem2').name)
        attrs_elem = root.find_first(name='Attrs')
        self.assertEqual('Attrs', attrs_elem.name)
        # TODO Allow attrib lookups without namespace prefix?
        self.assertEqual(
            'testns', attrs_elem.attributes.prefix('testns:attrib1'))
        self.assertEqual(
            'testns', attrs_elem.attributes.prefix('testns:attrib2'))
        self.assertEqual(
            'urn:test', attrs_elem.attributes.namespace_uri('testns:attrib1'))
        self.assertEqual(
            'urn:test', attrs_elem.attributes.namespace_uri('testns:attrib2'))
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot xmlns="urn:default" xmlns:testns="urn:test">\n'
            '    <testns:Elem1/>\n'
            '    <testns:Elem2/>\n'
            '    <Attrs testns:attrib1="value1" testns:attrib2="value2"/>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())
        # Attempts to use undefined namespace prefixes will fail
        xmlb = self.my_builder('DocRoot', ns_uri='urn:default')
        self.assertRaises(Exception,
            xmlb.e, ['missingns:Elem1'])
        self.assertRaises(Exception,
            xmlb.attrs, [{'missingns:attrib1': 'value1'}])
        # Element with literal namespace defn will use the ns as its default
        xmlb = self.my_builder('DocRoot', ns_uri='urn:default')
        xmlb.e('{urn:missing}Elem1')
        self.assertEqual(
            None, xmlb.root.find_first(name='Elem1').prefix)
        self.assertEqual(
            'urn:missing',
            xmlb.root.find_first(name='Elem1').namespace_uri)
        self.assertEqual(
            'urn:missing',
            xmlb.root.find_first(name='Elem1').attributes['xmlns'])
        # Automatically define prefix for attribute with literal namespace
        xmlb.attrs({'{urn:missing2}attrib1': 'value2'})
        self.assertEqual(
            'autoprefix0',
            xmlb.root.attributes.prefix('autoprefix0:attrib1'))
        self.assertEqual(
            'urn:missing2',
            xmlb.root.attributes.namespace_uri('autoprefix0:attrib1'))
        self.assertEqual(
            'urn:missing2',
            xmlb.root.attributes['xmlns:autoprefix0'])
        xmlb.attrs({'{urn:missing3}attrib2': 'value3'})
        self.assertEqual(
            'autoprefix1',
            xmlb.root.attributes.prefix('autoprefix1:attrib2'))
        self.assertEqual(
            'urn:missing3',
            xmlb.root.attributes.namespace_uri('autoprefix1:attrib2'))
        self.assertEqual(
            'urn:missing3',
            xmlb.root.attributes['xmlns:autoprefix1'])

    def test_cdata(self):
        # Aliases
        xmlb = self.my_builder('DocRoot')
        self.assertEqual(xmlb.cdata, xmlb.data)
        self.assertEqual(xmlb.cdata, xmlb.d)
        # Add text values to elements
        xmlb = (
            self.my_builder('DocRoot')
                .e('Elem1').t('<content/> as text').up()
                .e('Elem2').d('<content/> as cdata').up()
            )
        if self.adapter == LXMLAdapter:
            # TODO: lxml library does not support real cdata?
            self.assertEqual(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<DocRoot>\n'
                '    <Elem1>&lt;content/&gt; as text</Elem1>\n'
                '    <Elem2>&lt;content/&gt; as cdata</Elem2>\n'
                '</DocRoot>\n',
                xmlb.anchor_element.doc_xml())
        else:
            self.assertEqual(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<DocRoot>\n'
                '    <Elem1>&lt;content/&gt; as text</Elem1>\n'
                '    <Elem2><![CDATA[<content/> as cdata]]></Elem2>\n'
                '</DocRoot>\n',
                xmlb.anchor_element.doc_xml())

    def test_element_with_extra_kwargs(self):
        xmlb = (
            self.my_builder('DocRoot')
                # Include attributes
                .e('Elem', attributes=[('x', 1)]).up()
                .e('Elem', attributes={'my-attribute': 'value'}).up()
                # Include text
                .e('Elem', text='Text value').up()
                # Include attributes and text
                .e('Elem', attributes={'x': 1}, text='More text').up()
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <Elem x="1"/>\n'
            '    <Elem my-attribute="value"/>\n'
            '    <Elem>Text value</Elem>\n'
            '    <Elem x="1">More text</Elem>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())
        # Insert a new element before another
        xmlb = (
            self.my_builder('DocRoot')
                .e('FinalElement')
                .e('PenultimateElement', before_this_element=True)
                .e('ThirdLastElement', before_this_element=True)
            )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<DocRoot>\n'
            '    <ThirdLastElement/>\n'
            '    <PenultimateElement/>\n'
            '    <FinalElement/>\n'
            '</DocRoot>\n',
            xmlb.anchor_element.doc_xml())

    def test_unicode(self):
        ns_default = u'urn:默认'
        ns_custom = u'urn:習俗'
        # NOTE lxml doesn't support unicode namespace URIs
        if self.adapter == LXMLAdapter:
            ns_default = 'urn:default'
            ns_custom = 'urn:custom'
        xmlb = (
            self.my_builder(u'جذر', ns_uri=ns_default)
                .ns_prefix(u'důl', ns_custom)
                .e(u'důl:ぷㄩƦ').up()
                .e(u'yếutố1')
                    .attrs({u'תכונה': '1'})
                    .up()
                .e(u'yếutố2')
                    .attrs({u'důl:עודתכונה': u'tvö'})
            )
        self.assertEqual((
            u'<?xml version="1.0" encoding="utf-8"?>\n'
            u'<جذر xmlns="%(ns_default)s" xmlns:důl="%(ns_custom)s">\n'
            u'    <důl:ぷㄩƦ/>\n'
            u'    <yếutố1 תכונה="1"/>\n'
            u'    <yếutố2 důl:עודתכונה="tvö"/>\n'
            u'</جذر>\n') % {'ns_default': ns_default, 'ns_custom': ns_custom},
            xmlb.anchor_element.doc_xml())
        doc = xmlb.document
        self.assertEqual(u'جذر', doc.root.name)
        self.assertEqual(ns_default, doc.root.attributes[u'xmlns'])
        self.assertEqual(ns_custom, doc.root.attributes[u'xmlns:důl'])
        self.assertEqual(3, len(doc.find(ns_uri=ns_default)))
        self.assertEqual(1, len(doc.find(ns_uri=ns_custom)))
        self.assertEqual(u'1', doc.find_first(u'yếutố1').attributes[u'תכונה'])
        self.assertEqual(u'tvö',
            doc.find_first(u'yếutố2').attributes[u'důl:עודתכונה'])


class TestXmlDomBuilder(BaseBuilderNodesTest, unittest.TestCase):
    """
    Tests building with the standard library xml.dom module, or with any
    library that augments/clobbers this module.
    """

    @property
    def adapter(self):
        from xml4h.impls.xml_dom_minidom import XmlDomImplAdapter
        return XmlDomImplAdapter

    @property
    def my_builder(self):
        return functools.partial(builder, adapter=self.adapter)


class TestLXMLEtreeBuilder(BaseBuilderNodesTest, unittest.TestCase):
    """
    Tests building with the lxml (lxml.etree) library.
    """

    @property
    def adapter(self):
        from xml4h.impls.lxml_etree import LXMLAdapter
        if not LXMLAdapter.is_available():
            self.skipTest("lxml library is not installed")
        return LXMLAdapter

    @property
    def my_builder(self):
        return functools.partial(builder, adapter=self.adapter)


class TestDefaultImpl(BaseBuilderNodesTest, unittest.TestCase):
    """
    Tests building with the default implementation, whichever it is.
    """

    @property
    def adapter(self):
        return impl_preferred

    @property
    def my_builder(self):
        return functools.partial(builder)
