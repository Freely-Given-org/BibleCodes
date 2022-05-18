#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# BibleVersionCodesConverter.py
#
# Module handling BibleVersionCodes.xml to produce various derived export formats
#
# Copyright (C) 2022 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+BOS@gmail.com>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module to load BibleVersionCodes.xml file
    and list the contents in various derived forms.
"""
from gettext import gettext as _
from typing import Dict, List, Tuple
import os
import logging
from xml.etree.ElementTree import ElementTree
from collections import defaultdict

import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2022-05-18' # by RJH
SHORT_PROGRAM_NAME = "BibleVersionCodesConverter"
PROGRAM_NAME = "Bible Version Codes converter"
PROGRAM_VERSION = '0.01'
programNameVersion = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

debuggingThisModule = False



class BibleVersionCodesConverter:
    """
    Class for reading, validating, and converting BibleVersionCodes.
    This is only intended as a transitory class (used at start-up).
    The BibleVersionCodes class has functions more generally useful.
    """

    def __init__( self ) -> None: # We can't give this parameters because of the singleton
        """
        Constructor: expects the filepath of the source XML file.
        Loads (and crudely validates the XML file) into an element tree.
        """
        self._filenameBase = 'BibleVersionCodes'

        # These fields are used for parsing the XML
        self._treeTag = 'BibleVersionCodes'
        self._headerTag = 'header'
        self._mainElementTag = 'BibleVersionCodes'

        # These fields are used for automatically checking/validating the XML
        self._compulsoryAttributes = ()
        self._optionalAttributes = ()
        self._uniqueAttributes = self._compulsoryAttributes + self._optionalAttributes
        self._compulsoryElements = ( 'mainAbbreviation', 'versionName', 'languageCode', )
        self._optionalElements = ( 'publisherName', 'licence', 'webLink', )
        self._uniqueElements = ( 'mainAbbreviation', 'webLink', )

        # These are fields that we will fill later
        self._XMLheader, self._XMLTree = None, None
        self.__DataSets = {} # Used for import
        self.titleString = self.PROGRAM_VERSION = self.dateString = ''
    # end of BibleVersionCodesConverter.__init__


    def loadAndValidate( self, XMLFileOrFilepath=None ):
        """"
        Loads (and crudely validates the XML file) into an element tree.
            Allows the filepath of the source XML file to be specified, otherwise uses the default.
        """
        if self._XMLTree is None: # We mustn't have already have loaded the data
            if XMLFileOrFilepath is None:
                XMLFileOrFilepath = os.path.join('../sourceXML', self._filenameBase + '.xml')

            self.__load( XMLFileOrFilepath )
            if BibleOrgSysGlobals.strictCheckingFlag:
                self.__validate()
        else: # The data must have been already loaded
            if XMLFileOrFilepath is not None and XMLFileOrFilepath!=self.__XMLFileOrFilepath: logging.error( _("Bible books codes are already loaded -- your different filepath of {!r} was ignored").format( XMLFileOrFilepath ) )
        return self
    # end of BibleVersionCodesConverter.loadAndValidate


    def __load( self, XMLFileOrFilepath ):
        """
        Load the source XML file and remove the header from the tree.
        Also, extracts some useful elements from the header element.
        """
        assert XMLFileOrFilepath
        self.__XMLFileOrFilepath = XMLFileOrFilepath
        assert self._XMLTree is None or len(self._XMLTree)==0 # Make sure we're not doing this twice

        vPrint( 'Info', debuggingThisModule, _("Loading BibleVersionCodes XML file from {!r}…").format( self.__XMLFileOrFilepath ) )
        self._XMLTree = ElementTree().parse( self.__XMLFileOrFilepath )
        assert self._XMLTree # Fail here if we didn't load anything at all

        if self._XMLTree.tag == self._treeTag:
            header = self._XMLTree[0]
            if header.tag == self._headerTag:
                self.XMLheader = header
                self._XMLTree.remove( header )
                BibleOrgSysGlobals.checkXMLNoText( header, 'header' )
                BibleOrgSysGlobals.checkXMLNoTail( header, 'header' )
                BibleOrgSysGlobals.checkXMLNoAttributes( header, 'header' )
                if len(header)>1:
                    logging.info( _("Unexpected elements in header") )
                elif len(header)==0:
                    logging.info( _("Missing work element in header") )
                else:
                    work = header[0]
                    BibleOrgSysGlobals.checkXMLNoText( work, "work in header" )
                    BibleOrgSysGlobals.checkXMLNoTail( work, "work in header" )
                    BibleOrgSysGlobals.checkXMLNoAttributes( work, "work in header" )
                    if work.tag == "work":
                        self.PROGRAM_VERSION = work.find('version').text
                        self.dateString = work.find('date').text
                        self.titleString = work.find('title').text
                    else:
                        logging.warning( _("Missing work element in header") )
            else:
                logging.warning( _("Missing header element (looking for {!r} tag)".format( self._headerTag ) ) )
            if header.tail is not None and header.tail.strip(): logging.error( _("Unexpected {!r} tail data after header").format( header.tail ) )
        else:
            logging.error( _("Expected to load {!r} but got {!r}").format( self._treeTag, self._XMLTree.tag ) )
    # end of BibleVersionCodesConverter.__load


    def __validate( self ):
        """
        Check/validate the loaded data.
        """
        assert self._XMLTree

        uniqueDict = {}
        for elementName in self._uniqueElements: uniqueDict["Element_"+elementName] = []
        for attributeName in self._uniqueAttributes: uniqueDict["Attribute_"+attributeName] = []

        expectedID = 1
        for j,element in enumerate(self._XMLTree):
            if element.tag == self._mainElementTag:
                BibleOrgSysGlobals.checkXMLNoText( element, element.tag )
                BibleOrgSysGlobals.checkXMLNoTail( element, element.tag )
                if not self._compulsoryAttributes and not self._optionalAttributes: BibleOrgSysGlobals.checkXMLNoAttributes( element, element.tag )
                if not self._compulsoryElements and not self._optionalElements: BibleOrgSysGlobals.checkXMLNoSubelements( element, element.tag )

                # Check compulsory attributes on this main element
                for attributeName in self._compulsoryAttributes:
                    attributeValue = element.get( attributeName )
                    if attributeValue is None:
                        logging.error( _("Compulsory {!r} attribute is missing from {} element in record {}").format( attributeName, element.tag, j ) )
                    if not attributeValue:
                        logging.warning( _("Compulsory {!r} attribute is blank on {} element in record {}").format( attributeName, element.tag, j ) )

                # Check optional attributes on this main element
                for attributeName in self._optionalAttributes:
                    attributeValue = element.get( attributeName )
                    if attributeValue is not None:
                        if not attributeValue:
                            logging.warning( _("Optional {!r} attribute is blank on {} element in record {}").format( attributeName, element.tag, j ) )

                # Check for unexpected additional attributes on this main element
                for attributeName in element.keys():
                    attributeValue = element.get( attributeName )
                    if attributeName not in self._compulsoryAttributes and attributeName not in self._optionalAttributes:
                        logging.warning( _("Additional {!r} attribute ({!r}) found on {} element in record {}").format( attributeName, attributeValue, element.tag, j ) )

                # Check the attributes that must contain unique information (in that particular field -- doesn't check across different attributes)
                for attributeName in self._uniqueAttributes:
                    attributeValue = element.get( attributeName )
                    if attributeValue is not None:
                        if attributeValue in uniqueDict["Attribute_"+attributeName]:
                            logging.error( _("Found {!r} data repeated in {!r} field on {} element in record {}").format( attributeValue, attributeName, element.tag, j ) )
                        uniqueDict["Attribute_"+attributeName].append( attributeValue )

                # Get the referenceAbbreviation to use as a record ID
                ID = element.find("referenceAbbreviation").text

                # Check compulsory elements
                for elementName in self._compulsoryElements:
                    foundElement = element.find( elementName )
                    if foundElement is None:
                        logging.error( _("Compulsory {!r} element is missing in record with ID {!r} (record {})").format( elementName, ID, j ) )
                    else:
                        BibleOrgSysGlobals.checkXMLNoTail( foundElement, foundElement.tag + " in " + element.tag )
                        BibleOrgSysGlobals.checkXMLNoAttributes( foundElement, foundElement.tag + " in " + element.tag )
                        BibleOrgSysGlobals.checkXMLNoSubelements( foundElement, foundElement.tag + " in " + element.tag )
                        if not foundElement.text:
                            logging.warning( _("Compulsory {!r} element is blank in record with ID {!r} (record {})").format( elementName, ID, j ) )

                # Check optional elements
                for elementName in self._optionalElements:
                    foundElement = element.find( elementName )
                    if foundElement is not None:
                        BibleOrgSysGlobals.checkXMLNoTail( foundElement, foundElement.tag + " in " + element.tag )
                        BibleOrgSysGlobals.checkXMLNoAttributes( foundElement, foundElement.tag + " in " + element.tag )
                        BibleOrgSysGlobals.checkXMLNoSubelements( foundElement, foundElement.tag + " in " + element.tag )
                        if not foundElement.text:
                            logging.warning( _("Optional {!r} element is blank in record with ID {!r} (record {})").format( elementName, ID, j ) )

                # Check for unexpected additional elements
                for subelement in element:
                    if subelement.tag not in self._compulsoryElements and subelement.tag not in self._optionalElements:
                        logging.warning( _("Additional {!r} element ({!r}) found in record with ID {!r} (record {})").format( subelement.tag, subelement.text, ID, j ) )

                # Check the elements that must contain unique information (in that particular element -- doesn't check across different elements)
                for elementName in self._uniqueElements:
                    if element.find( elementName ) is not None:
                        text = element.find( elementName ).text
                        if text in uniqueDict["Element_"+elementName]:
                            logging.error( _("Found {!r} data repeated in {!r} element in record with ID {!r} (record {})").format( text, elementName, ID, j ) )
                        uniqueDict["Element_"+elementName].append( text )
            else:
                logging.warning( _("Unexpected element: {} in record {}").format( element.tag, j ) )
            if element.tail is not None and element.tail.strip(): logging.error( _("Unexpected {!r} tail data after {} element in record {}").format( element.tail, element.tag, j ) )
        if self._XMLTree.tail is not None and self._XMLTree.tail.strip(): logging.error( _("Unexpected {!r} tail data after {} element").format( self._XMLTree.tail, self._XMLTree.tag ) )
    # end of BibleVersionCodesConverter.__validate


    def __str__( self ) -> str:
        """
        This method returns the string representation of a Bible version code.

        @return: the name of a Bible object formatted as a string
        @rtype: string
        """
        indent = 2
        result = "BibleVersionCodesConverter object"
        if self.titleString: result += ('\n' if result else '') + ' '*indent + _("Title: {}").format( self.titleString )
        if self.PROGRAM_VERSION: result += ('\n' if result else '') + ' '*indent + _("Version: {}").format( self.PROGRAM_VERSION )
        if self.dateString: result += ('\n' if result else '') + ' '*indent + _("Date: {}").format( self.dateString )
        if self._XMLTree is not None: result += ('\n' if result else '') + ' '*indent + _("Number of entries = {:,}").format( len(self._XMLTree) )
        return result
    # end of BibleVersionCodesConverter.__str__


    def __len__( self ):
        """ Returns the number of books version codes loaded. """
        return len( self._XMLTree )
    # end of BibleVersionCodesConverter.__len__


    def importDataToPython( self ):
        """
        Loads (and pivots) the data (not including the header) into suitable Python containers to use in a Python program.
        (Of course, you can just use the elementTree in self._XMLTree if you prefer.)
        """
        def makeList( parameter1, parameter2 ):
            """
            Returns a list containing all parameters. Parameter1 may already be a list.
            """
            if isinstance( parameter1, list ):
                #assert parameter2 not in parameter1
                parameter1.append( parameter2 )
                return parameter1
            else:
                return [ parameter1, parameter2 ]
        # end of makeList


        def addToAllCodesDict( givenUCAbbreviation, abbrevType, initialAllAbbreviationsDict ):
            """
            Checks if the given abbreviation is already in the dictionary with a different value.
            """
            if givenUCAbbreviation in initialAllAbbreviationsDict and initialAllAbbreviationsDict[givenUCAbbreviation] != referenceAbbreviation:
                logging.warning( _("This {} {!r} abbreviation ({}) already assigned to {!r}").format( abbrevType, givenUCAbbreviation, referenceAbbreviation, initialAllAbbreviationsDict[givenUCAbbreviation] ) )
                initialAllAbbreviationsDict[givenUCAbbreviation] = 'MultipleValues'
            else: initialAllAbbreviationsDict[givenUCAbbreviation] = referenceAbbreviation
        # end of addToAllCodesDict


        assert self._XMLTree
        if self.__DataSets: # We've already done an import/restructuring -- no need to repeat it
            return self.__DataSets

        # We'll create a number of lists and dictionaries with different elements as the key
        myAbbrevList, myAbbrevDict = [], {}
        myNameDict, myLanguageDict, myPublisherDict, myLicenseDict, myWebLinkDict = \
            defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
        for element in self._XMLTree:
            # Get the required information out of the tree for this element
            # Start with the compulsory elements
            mainAbbreviation = element.find('mainAbbreviation').text
            versionName = element.find('versionName').text # In the original language
            languageCode = element.find('languageCode').text # This name is really just a comment element

            # The optional elements are set to None if they don't exist
            publisherName = None if element.find('publisherName') is None else element.find('publisherName').text
            licence = None if element.find('licence') is None else element.find('licence').text
            webLink = None if element.find('webLink') is None else element.find('webLink').text

            # Now put it into my dictionaries for easy access
            # This part should be customized or added to for however you need to process the data
            #   Add .upper() if you require the abbreviations to be uppercase (or .lower() for lower case)
            #   The mainAbbreviation is UPPER CASE by definition
            myAbbrevList.append( mainAbbreviation )

            entry = { 'versionName':versionName, 'languageCode':languageCode, }
            if publisherName: entry['publisherName'] = publisherName
            if licence: entry['licence'] = licence
            if webLink: entry['webLink'] = webLink
            myAbbrevDict[mainAbbreviation] = entry

            entry = { 'mainAbbreviation':mainAbbreviation, 'languageCode':languageCode, }
            if publisherName: entry['publisherName'] = publisherName
            if licence: entry['licence'] = licence
            if webLink: entry['webLink'] = webLink
            myNameDict[versionName].append( entry )

            entry = { 'mainAbbreviation':mainAbbreviation, 'versionName':versionName, }
            if publisherName: entry['publisherName'] = publisherName
            if licence: entry['licence'] = licence
            if webLink: entry['webLink'] = webLink
            myLanguageDict[languageCode].append( entry )

            if publisherName:
                entry = { 'mainAbbreviation':mainAbbreviation, 'versionName':versionName, 'languageCode':languageCode, }
                if licence: entry['licence'] = licence
                if webLink: entry['webLink'] = webLink
                myPublisherDict[publisherName].append( entry )

            if licence:
                entry = { 'mainAbbreviation':mainAbbreviation, 'versionName':versionName, 'languageCode':languageCode, }
                if publisherName: entry['publisherName'] = publisherName
                if webLink: entry['webLink'] = webLink
                myLicenseDict[licence].append( entry )

            if webLink:
                entry = { 'mainAbbreviation':mainAbbreviation, 'versionName':versionName, 'languageCode':languageCode, }
                if publisherName: entry['publisherName'] = publisherName
                if licence: entry['licence'] = licence
                myWebLinkDict[webLink].append( entry )

        self.__DataSets = { 'AbbreviationsList': sorted(myAbbrevList),
                            'AbbreviationsDict': myAbbrevDict,
                            'NamesDict': myNameDict,
                            'LanguageDict': myLanguageDict,
                            'PublisherDict': myPublisherDict,
                            'LicenceDict': myLicenseDict,
                            'WebLinkDict': myWebLinkDict, }

        return self.__DataSets # Just delete any of the dictionaries that you don't need
    # end of BibleVersionCodesConverter.importDataToPython


    def pickle( self, filepath=None ):
        """
        Writes the information tables to a .pickle file that can be easily loaded into a Python3 program.
        """
        import pickle

        assert self._XMLTree
        self.importDataToPython()
        assert self.__DataSets

        if not filepath:
            folderpath = Path('../derivedFormats/')
                            # TODO: What was this all about ???
                            # if isinstance( self.__XMLFileOrFilepath, (str,Path) ) \
                            # else BibleOrgSysGlobals.DEFAULT_WRITEABLE_CACHE_FOLDERPATH
            if not os.path.exists( folderpath ): os.mkdir( folderpath )
            filepath = os.path.join( folderpath, self._filenameBase + '_Tables.pickle' )
        vPrint( 'Quiet', debuggingThisModule, _("Exporting to {}…").format( filepath ) )
        with open( filepath, 'wb' ) as myFile:
            pickle.dump( self.__DataSets, myFile )
    # end of BibleVersionCodesConverter.pickle


    def exportDataToPython( self, filepath=None ):
        """
        Writes the information tables to a .py file that can be cut and pasted into a Python program.
        """
        def exportPythonDictOrList( theFile, theDictOrList, dictName, keyComment, fieldsComment ):
            """Exports theDictOrList to theFile."""
            assert theDictOrList
            raise Exception( "Not written yet" )
            for dictKey in theDict.keys(): # Have to iterate this :(
                fieldsCount = len( theDict[dictKey] )
                break # We only check the first (random) entry we get
            theFile.write( "{} = {{\n  # Key is {}\n  # Fields ({}) are: {}\n".format( dictName, keyComment, fieldsCount, fieldsComment ) )
            for dictKey in sorted(theDict.keys()):
                theFile.write( '  {}: {},\n'.format( repr(dictKey), repr(theDict[dictKey]) ) )
            theFile.write( "}}\n# end of {} ({} entries)\n\n".format( dictName, len(theDict) ) )
        # end of exportPythonDictOrList


        assert self._XMLTree
        self.importDataToPython()
        assert self.__DataSets

        if not filepath:
            folderpath = Path('../derivedFormats/')
            if not os.path.exists( folderpath ): os.mkdir( folderpath )
            filepath = os.path.join( folderpath, self._filenameBase + '_Tables.py' )
        vPrint( 'Quiet', debuggingThisModule, _("Exporting to {}…").format( filepath ) )
        with open( filepath, 'wt', encoding='utf-8' ) as myFile:
            myFile.write( "# {}\n#\n".format( filepath ) )
            myFile.write( "# This UTF-8 file was automatically generated by BibleVersionCodes.py V{} on {}\n#\n".format( PROGRAM_VERSION, datetime.now() ) )
            if self.titleString: myFile.write( "# {} data\n".format( self.titleString ) )
            if self.PROGRAM_VERSION: myFile.write( "#  Version: {}\n".format( self.PROGRAM_VERSION ) )
            if self.dateString: myFile.write( "#  Date: {}\n#\n".format( self.dateString ) )
            myFile.write( "#   {} {} loaded from the original XML file.\n#\n\n".format( len(self._XMLTree), self._treeTag ) )
            mostEntries = "0=referenceNumber (integer 1..999), 1=referenceAbbreviation/BBB (3-uppercase characters)"
            dictInfo = {  }
            for dictName,dictData in self.__DataSets.items():
                exportPythonDictOrList( myFile, dictData, dictName, dictInfo[dictName][0], dictInfo[dictName][1] )
            myFile.write( "# end of {}".format( os.path.basename(filepath) ) )
    # end of BibleVersionCodesConverter.exportDataToPython


    def exportDataToJSON( self, filepath=None ):
        """
        Writes the information tables to a .json file that can be easily loaded into a Java program.

        See https://en.wikipedia.org/wiki/JSON.
        """
        import json

        assert self._XMLTree
        self.importDataToPython()
        assert self.__DataSets

        if not filepath:
            folderpath = Path('../derivedFormats/')
            if not os.path.exists( folderpath ): os.mkdir( folderpath )
            filepath = os.path.join( folderpath, self._filenameBase + '_Tables.json' )
        vPrint( 'Quiet', debuggingThisModule, _("Exporting to {}…").format( filepath ) )
        with open( filepath, 'wt', encoding='utf-8' ) as myFile:
            # WARNING: The following code converts int referenceNumber keys from int to str !!!
            json.dump( self.__DataSets, myFile, ensure_ascii=False, indent=2 )
    # end of BibleVersionCodesConverter.exportDataToJSON


    def exportDataToC( self, filepath=None ):
        """
        Writes the information tables to a .h and .c files that can be included in c and c++ programs.

        NOTE: The (optional) filepath should not have the file extension specified -- this is added automatically.
        """
        def exportPythonDict( hFile, cFile, theDict, dictName, sortedBy, structure ):
            """ Exports theDict to the .h and .c files. """
            def convertEntry( entry ):
                """ Convert special characters in an entry… """
                result = ""
                if isinstance( entry, str ):
                    result = entry
                elif isinstance( entry, tuple ):
                    for field in entry:
                        if result: result += ", " # Separate the fields
                        if field is None: result += '""'
                        elif isinstance( field, str): result += '"' + str(field).replace('"','\\"') + '"'
                        elif isinstance( field, int): result += str(field)
                        elif isinstance( field, list): raise Exception( "Not written yet (list1)" )
                        else: logging.error( _("Cannot convert unknown field type {!r} in tuple entry {!r}").format( field, entry ) )
                elif isinstance( entry, dict ):
                    for key in sorted(entry.keys()):
                        field = entry[key]
                        if result: result += ", " # Separate the fields
                        if field is None: result += '""'
                        elif isinstance( field, str): result += '"' + str(field).replace('"','\\"') + '"'
                        elif isinstance( field, int): result += str(field)
                        elif isinstance( field, list): raise Exception( "Not written yet (list2)" )
                        else: logging.error( _("Cannot convert unknown field type {!r} in dict entry {!r}").format( field, entry ) )
                else:
                    logging.error( _("Can't handle this type of entry yet: {}").format( repr(entry) ) )
                return result
            # end of convertEntry

            for dictKey in theDict.keys(): # Have to iterate this :(
                fieldsCount = len( theDict[dictKey] ) + 1 # Add one since we include the key in the count
                break # We only check the first (random) entry we get

            #hFile.write( "typedef struct {}EntryStruct { {} } {}Entry;\n\n".format( dictName, structure, dictName ) )
            hFile.write( "typedef struct {}EntryStruct {{\n".format( dictName ) )
            for declaration in structure.split(';'):
                adjDeclaration = declaration.strip()
                if adjDeclaration: hFile.write( "    {};\n".format( adjDeclaration ) )
            hFile.write( "}} {}Entry;\n\n".format( dictName ) )

            cFile.write( "const static {}Entry\n {}[{}] = {{\n  // Fields ({}) are {}\n  // Sorted by {}\n".format( dictName, dictName, len(theDict), fieldsCount, structure, sortedBy ) )
            for dictKey in sorted(theDict.keys()):
                if isinstance( dictKey, str ):
                    cFile.write( "  {{\"{}\", {}}},\n".format( dictKey, convertEntry(theDict[dictKey]) ) )
                elif isinstance( dictKey, int ):
                    cFile.write( "  {{{}, {}}},\n".format( dictKey, convertEntry(theDict[dictKey]) ) )
                else:
                    logging.error( _("Can't handle this type of key data yet: {}").format( dictKey ) )
            cFile.write( "]}}; // {} ({} entries)\n\n".format( dictName, len(theDict) ) )
        # end of exportPythonDict


        assert self._XMLTree
        self.importDataToPython()
        assert self.__DataSets

        if not filepath:
            folderpath = Path('../derivedFormats/')
            if not os.path.exists( folderpath ): os.mkdir( folderpath )
            filepath = os.path.join( folderpath, self._filenameBase + '_Tables' )
        hFilepath = filepath + '.h'
        cFilepath = filepath + '.c'
        vPrint( 'Quiet', debuggingThisModule, _("Exporting to {}…").format( cFilepath ) ) # Don't bother telling them about the .h file
        ifdefName = self._filenameBase.upper() + "_Tables_h"

        with open( hFilepath, 'wt', encoding='utf-8' ) as myHFile, \
             open( cFilepath, 'wt', encoding='utf-8' ) as myCFile:
            myHFile.write( "// {}\n//\n".format( hFilepath ) )
            myCFile.write( "// {}\n//\n".format( cFilepath ) )
            lines = "// This UTF-8 file was automatically generated by BibleVersionCodes.py V{} on {}\n//\n".format( PROGRAM_VERSION, datetime.now() )
            myHFile.write( lines ); myCFile.write( lines )
            if self.titleString:
                lines = "// {} data\n".format( self.titleString )
                myHFile.write( lines ); myCFile.write( lines )
            if self.PROGRAM_VERSION:
                lines = "//  Version: {}\n".format( self.PROGRAM_VERSION )
                myHFile.write( lines ); myCFile.write( lines )
            if self.dateString:
                lines = "//  Date: {}\n//\n".format( self.dateString )
                myHFile.write( lines ); myCFile.write( lines )
            myCFile.write( "//   {} {} loaded from the original XML file.\n//\n\n".format( len(self._XMLTree), self._treeTag ) )
            myHFile.write( "\n#ifndef {}\n#define {}\n\n".format( ifdefName, ifdefName ) )
            myCFile.write( '#include "{}"\n\n'.format( os.path.basename(hFilepath) ) )

            CHAR = "const unsigned char"
            BYTE = "const int"
            dictInfo = {
                "referenceNumberDict":("referenceNumber (integer 1..255)",
                    "{} referenceNumber; {}* ByzantineAbbreviation; {}* CCELNumberString; {}* NETBibleAbbreviation; {}* OSISAbbreviation; {} USFMAbbreviation[3+1]; {} USFMNumberString[2+1]; {}* SBLAbbreviation; {}* SwordAbbreviation; {}* bookNameEnglishGuide; {}* numExpectedChapters; {}* possibleAlternativeBooks; {} referenceAbbreviation[3+1];"
                   .format(BYTE, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR ) ),
                "referenceAbbreviationDict":("referenceAbbreviation",
                    "{} referenceAbbreviation[3+1]; {}* ByzantineAbbreviation; {}* CCELNumberString; {} referenceNumber; {}* NETBibleAbbreviation; {}* OSISAbbreviation; {} USFMAbbreviation[3+1]; {} USFMNumberString[2+1]; {}* SBLAbbreviation; {}* SwordAbbreviation; {}* bookNameEnglishGuide; {}* numExpectedChapters; {}* possibleAlternativeBooks;"
                   .format(CHAR, CHAR, CHAR, BYTE, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR, CHAR ) ),
                "sequenceList":("sequenceList",),
                "CCELDict":("CCELNumberString", "{}* CCELNumberString; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "SBLAbbreviationDict":("SBLAbbreviation", "{}* SBLAbbreviation; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "OSISAbbreviationDict":("OSISAbbreviation", "{}* OSISAbbreviation; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "SwordAbbreviationDict":("SwordAbbreviation", "{}* SwordAbbreviation; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "USFMAbbreviationDict":("USFMAbbreviation", "{} USFMAbbreviation[3+1]; {} referenceNumber; {} referenceAbbreviation[3+1]; {} USFMNumberString[2+1];".format(CHAR,BYTE,CHAR,CHAR) ),
                "USFMNumberDict":("USFMNumberString", "{} USFMNumberString[2+1]; {} referenceNumber; {} referenceAbbreviation[3+1]; {} USFMAbbreviation[3+1];".format(CHAR,BYTE,CHAR,CHAR) ),
                "USXNumberDict":("USXNumberString", "{} USXNumberString[3+1]; {} referenceNumber; {} referenceAbbreviation[3+1]; {} USFMAbbreviation[3+1];".format(CHAR,BYTE,CHAR,CHAR) ),
                "UnboundCodeDict":("UnboundCodeString", "{} UnboundCodeString[3+1]; {} referenceNumber; {} referenceAbbreviation[3+1]; {} USFMAbbreviation[3+1];".format(CHAR,BYTE,CHAR,CHAR) ),
                "BibleditNumberDict":("BibleditNumberString", "{} BibleditNumberString[2+1]; {} referenceNumber; {} referenceAbbreviation[3+1]; {} USFMAbbreviation[3+1];".format(CHAR,BYTE,CHAR,CHAR) ),
                "NETBibleAbbreviationDict":("NETBibleAbbreviation", "{}* NETBibleAbbreviation; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "DrupalBibleAbbreviationDict":("DrupalBibleAbbreviation", "{}* DrupalBibleAbbreviation; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "ByzantineAbbreviationDict":("ByzantineAbbreviation", "{}* ByzantineAbbreviation; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "EnglishNameDict":("bookNameEnglishGuide", "{}* bookNameEnglishGuide; {} referenceNumber; {} referenceAbbreviation[3+1];".format(CHAR,BYTE,CHAR) ),
                "initialAllAbbreviationsDict":("abbreviation", "{}* abbreviation; {} referenceAbbreviation[3+1];".format(CHAR,CHAR) ) }

            for dictName,dictData in self.__DataSets.items():
                exportPythonDict( myHFile, myCFile, dictData, dictName, dictInfo[dictName][0], dictInfo[dictName][1] )

            myHFile.write( "#endif // {}\n\n".format( ifdefName ) )
            myHFile.write( "// end of {}".format( os.path.basename(hFilepath) ) )
            myCFile.write( "// end of {}".format( os.path.basename(cFilepath) ) )
    # end of BibleVersionCodesConverter.exportDataToC
# end of BibleVersionCodesConverter class



def briefDemo() -> None:
    """
    Main program to handle command line parameters and then run what they want.
    """
    BibleOrgSysGlobals.introduceProgram( __name__, programNameVersion, LAST_MODIFIED_DATE )

    if BibleOrgSysGlobals.commandLineArguments.export:
        bbcc = BibleVersionCodesConverter().loadAndValidate() # Load the XML
        # bbcc.pickle() # Produce a pickle output file
        # bbcc.exportDataToJSON() # Produce a json output file
        # bbcc.exportDataToPython() # Produce the .py tables
        # bbcc.exportDataToC() # Produce the .h and .c tables

    else: # Must be demo mode
        # Demo the converter object
        bbcc = BibleVersionCodesConverter().loadAndValidate() # Load the XML
        vPrint( 'Quiet', debuggingThisModule, bbcc ) # Just print a summary
        OAD = bbcc.importDataToPython()['OSISAbbreviationDict']
        vPrint( 'Quiet', debuggingThisModule, "\nSample output:" )
        vPrint( 'Quiet', debuggingThisModule, f"\nOSISAbbreviationDict: ({len(OAD)}) {sorted(OAD)}" )
        vPrint( 'Quiet', debuggingThisModule, f"\n{OAD['WIS']=}" )
# end of BibleVersionCodesConverter.briefDemo

def fullDemo() -> None:
    """
    Full demo to check class is working
    """
    BibleOrgSysGlobals.introduceProgram( __name__, programNameVersion, LAST_MODIFIED_DATE )

    bbcc = BibleVersionCodesConverter().loadAndValidate() # Load the XML
    if BibleOrgSysGlobals.commandLineArguments.export:
        bbcc.pickle() # Produce a pickle output file
        bbcc.exportDataToJSON() # Produce a json output file
        # bbcc.exportDataToPython() # Produce the .py tables
        # bbcc.exportDataToC() # Produce the .h and .c tables

    else: # Must be demo mode
        # Demo the converter object
        vPrint( 'Quiet', debuggingThisModule, bbcc ) # Just print a summary
        importedData = bbcc.importDataToPython()
        vPrint( 'Quiet', debuggingThisModule, "\nSample output:" )
        allKeys = importedData.keys()
        vPrint( 'Quiet', debuggingThisModule, f"\nallKeys: ({len(allKeys)}) {allKeys}" )
        abbreviationsList = importedData['AbbreviationsList']
        vPrint( 'Quiet', debuggingThisModule, f"\nAbbreviations: ({len(abbreviationsList)}) {abbreviationsList}" )
        abbreviationsDict = importedData['AbbreviationsDict']
        vPrint( 'Quiet', debuggingThisModule, f"\nAbbreviations: ({len(abbreviationsDict)}) OET = {abbreviationsDict['OET']}" )
        namesDict = importedData['NamesDict']
        vPrint( 'Quiet', debuggingThisModule, f"\nNames: ({len(namesDict)}) KJV = {namesDict['King James Version']}" )
        languagesDict = importedData['LanguageDict']
        vPrint( 'Quiet', debuggingThisModule, f"\nLanguages: ({len(languagesDict)}) {sorted(languagesDict.keys())}\n  hbo = {languagesDict['hbo']}" )
        publishersDict = importedData['PublisherDict']
        vPrint( 'Quiet', debuggingThisModule, f"\nPublishers: ({len(publishersDict)}) {sorted(publishersDict.keys())}" )
        licenceDict = importedData['LicenceDict']
        vPrint( 'Quiet', debuggingThisModule, f"\nLicences: ({len(licenceDict)}) {sorted(licenceDict.keys())}\n  PD = {licenceDict['Public Domain']}" )
        webLinksDict = importedData['WebLinkDict']
        vPrint( 'Quiet', debuggingThisModule, f"\nWebLinks: ({len(webLinksDict)}) {sorted(webLinksDict.keys())}" )
# end of BibleVersionCodesConverter.fullDemo

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=True )

    fullDemo()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of BibleVersionCodesConverter.py
