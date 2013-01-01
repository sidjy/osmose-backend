#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Frederic Rodrigo 2013                                      ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

import OsmSax


class ErrorFile:

    def __init__(self, config):
        self.config = config
        self.geom_type_renderer = {"node": self.node, "way": self.way, "relation": self.relation, "position": self.position}

    def analysers(self, args):
        self.outxml = OsmSax.OsmSaxWriter(open(self.config.dst, "w"), "UTF-8")
        self.outxml.startDocument()
        self.outxml.startElement("analysers", args)

    def analysers_end(self):
        self.outxml.endElement("analysers")
        self.outxml._out.close()

    def analyser(self, mode, args):
        self.outxml.startElement(mode, args)

    def analyser_end(self, mode):
        self.outxml.endElement(mode)

    def classs(self, id, item, level, tag, langs):
        options = {"id":str(id), "item": str(item)}
        if level:
            options["level"] = str(level)
        if tag:
            options["tag"] = ",".join(tag)
        self.outxml.startElement("class", options)
        for lang in langs:
            self.outxml.Element("classtext", {"lang":lang, "title":langs[lang]})
        self.outxml.endElement("class")

    def delete(self, t, id):
        self.outxml.Element("delete", {"type": t, "id": str(id)})

    def error(self, classs, subclass, text, res, fixType, fix, geom):
        if subclass:
            self.outxml.startElement("error", {"class":str(classs), "subclass":str(subclass)})
        else:
            self.outxml.startElement("error", {"class":str(classs)})
        for type in geom:
            for g in geom[type]:
                self.geom_type_renderer[type](g)
        for lang in text:
            self.outxml.Element("text", {"lang":lang, "value":text[lang]})
        if fix:
            self.dumpxmlfix(res, fixType, fix)
        self.outxml.endElement("error")

    def node(self, args):
        self.outxml.NodeCreate(args)

    def way(self, res):
        self.outxml.WayCreate(args)

    def relation(self, args):
        self.outxml.RelationCreate(args)

    def position(self, args):
        self.outxml.Element("location", args)

    FixTable = {'~':'modify', '+':'create', '-':'delete'}

    def fixdiff(self, fixes):
        """
        Normalise fix in e
        Normal form is [[{'+':{'k1':'v1', 'k2', 'v2'}, '-':{'k3':'v3'}, '~':{'k4','v4'}}, {...}]]
        Array of diff way to fix -> Array of fix for object part of error -> Dict for diff actions -> Dict for tags
        """
        if not isinstance(fixes, list):
            fixes = [[fixes]]
        elif not isinstance(fixes[0], list):
            # Default one level array is different way of fix
            fixes = map(lambda x: [x], fixes)
        return map(lambda fix:
            map(lambda f:
                None if f == None else (f if f.has_key('~') or f.has_key('-') or f.has_key('+') else {'~': f}),
                fix),
            fixes)

    def dumpxmlfix(self, res, fixesType, fixes):
        fixes = self.fixdiff(fixes)
        self.outxml.startElement("fixes", {})
        for fix in fixes:
            self.outxml.startElement("fix", {})
            i = 0
            for f in fix:
                if f != None and i < len(fixesType):
                    type = fixesType[i]
                    self.outxml.startElement(type, {'id': str(res[i])})
                    for opp, tags in f.items():
                        for k in tags:
                            if opp in '~+':
                                self.outxml.Element('tag', {'action': self.FixTable[opp], 'k': k, 'v': tags[k]})
                            else:
                                self.outxml.Element('tag', {'action': self.FixTable[opp], 'k': k})
                    self.outxml.endElement(type)
                i += 0
            self.outxml.endElement('fix')
        self.outxml.endElement('fixes')


if __name__ == "__main__":
    import pprint
    a = ErrorFile(None)
    def check(b, c):
        d = a.fixdiff(b)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(d)
        if d != c:
            raise Exception("fixdiff Excepted %s to %s but get %s" % (b, c, d) )
    check([[None]], [[None]] )
    check({"t": "v"}, [[{"~": {"t": "v"}}]] )
    check({"~": {"t": "v"}}, [[{"~": {"t": "v"}}]] )
    check({"~": {"t": "v"}, "+": {"t": "v"}}, [[{"~": {"t": "v"}, "+": {"t": "v"}}]] )
    check([{"~": {"t": "v"}, "+": {"t": "v"}}], [[{"~": {"t": "v"}, "+": {"t": "v"}}]] )
    check([{"~": {"t": "v"}}, {"+": {"t": "v"}}], [[{"~": {"t": "v"}}], [{"+": {"t": "v"}}]] )
    check([[{"t": "v"}], [{"t": "v"}]], [[{"~": {"t": "v"}}], [{"~": {"t": "v"}}]] )
    check([[None, {"t": "v"}]], [[None, {"~": {"t": "v"}}]] )
