# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Animove
                                 A QGIS plugin
 AniMove for QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-09
        copyright            : (C) 2021 by Matteo Ghetta (Faunalia)
        email                : matteo.ghetta@faunalia.eu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Matteo Ghetta (Faunalia)'
__date__ = '2021-07-09'
__copyright__ = '(C) 2021 by Matteo Ghetta (Faunalia)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon,QColor



from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsMessageLog,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingLayerPostProcessorInterface,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsPointXY,
                       QgsDistanceArea,
                       QgsGeometry,
                       QgsSymbol,
                       QgsProcessingUtils,
                       QgsFeature,
                       QgsRendererCategory,
                       QgsProcessingParameterFeatureSource,
                       QgsCategorizedSymbolRenderer,
                       QgsProcessingParameterFeatureSink)

import os

class AnimoveMCP(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    FIELD = 'FIELD'
    PERCENT = 'PERCENT'
    OUTPUT = 'OUTPUT'

    dest_id=0

    def initAlgorithm(self, config):

        # input point layer
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT,
                description=self.tr('Input layer'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )

        # input point layer field
        self.addParameter(
            QgsProcessingParameterField(
                name=self.FIELD,
                description=self.tr('Vector Layer Field'),
                parentLayerParameterName=self.INPUT
            )
        )

        # percent numeric value
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.PERCENT,
                description=self.tr('Percent of fixes'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=95,
                minValue=5,
                maxValue=100

            )
        )

       
        # output sink
        self.addParameter(
           QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('OUTPUTLAYER'),
                QgsProcessing.TypeVectorPolygon
            )
        )

      

        

      
    def processAlgorithm(self, parameters, context, feedback):

        # get reference of the input layer
        input_layer = self.parameterAsSource(
            parameters, 
            self.INPUT, 
            context
        )

        # get the reference of the input fields
        input_fields = self.parameterAsFields(
            parameters,
            self.FIELD,
            context
        )
        # get the single field name from the list
        input_field = input_fields[0]

        # get the reference of the percentage number
        perc = self.parameterAsInt(
            parameters,
            self.PERCENT,
            context
        )

        # create the sink
        
        # first the fields
        fields = QgsFields()
        fields.append(QgsField('ID', QVariant.String))
        fields.append(QgsField('Area', QVariant.Double))
        fields.append(QgsField('Perim', QVariant.Double))
        fields.append(QgsField('Color', QVariant.Double))

       

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.MultiPolygon, # polygon layer
            input_layer.sourceCrs()  # same CRS of the input layer
        )
        
        # calculte how many unique values are in the input field
        index = input_layer.fields().indexOf(input_field) # get the index of the field
        uniqueValues = input_layer.uniqueValues(index) # this is a set object
       
        # initialize QgsDistanceArea to measure the lines afterwards
        distArea = QgsDistanceArea()
        distArea.setSourceCrs(input_layer.sourceCrs(), context.transformContext())
        distArea.setEllipsoid(context.project().ellipsoid())



        total = 100 / len(uniqueValues) if uniqueValues else 0

        # loop into the unique values
        feedback.pushInfo(self.tr('Calculating the MCP Points'))
        for current, value in enumerate(uniqueValues):

            if feedback.isCanceled():
                break

            nElement = 0
            hull = []
            cx = 0.00  # x of mean coodinate
            cy = 0.00  # y of mean coordinate
            nf = 0
            

            
         
            # loop into the input layer features
            for feature in input_layer.getFeatures():
                
               

              

                # get the value of the input field for each feature
                fieldValue = feature[f"{input_field}"]

          
                
                # test if the value is the same of the unique value
                if fieldValue == value:

                    # get the geometry as QgsPointXY
                    try:
                       
                        point = feature.geometry().asPoint()
                        cx += point.x()
                        cy += point.y()
                        nf += 1
                    except Exception:
                      
                        continue
            try:
                cx = (cx / nf)
                cy = (cy / nf)
                meanPoint = QgsPointXY(cx, cy)
            except ZeroDivisionError:
                continue
           

            # initialize dictionary to store geometries and distances
            distanceGeometryMap = {}

            # loop in the input layer features (again)
            for feature in input_layer.getFeatures():

                # get the attribute of the input field for each feature
                fieldValue = feature[f"{input_field}"]

                # test if the value is the same of the unique value
                if fieldValue == value:

                    nElement += 1
                    geometry = QgsGeometry(feature.geometry())
                    # measure the distance from the mean point and each feature point (in meters)
                    try:
                        distance = distArea.measureLine(meanPoint, geometry.asPoint())

                        # add the values in to dictionary
                        distanceGeometryMap[distance] = geometry

                        # directly append the QgsPointXY to the hull list if the percentage chosen is 100
                        if perc == 100:
                            points = geometry.asPoint()
                            hull.append(points)

                    except ValueError:
                        continue
                
            # if the percentage chosen is not 100 call the function to add the QgsPointXY to the hull list
            if perc != 100:
                hull = self.percpoints(perc, distanceGeometryMap, nElement)
                
            # if the hull list has more than 2 elements (that is, we have at least 3 QgsPointXY to create a polygon)
            if len(hull) >= 3:

                    # initialize the empty QgsFeature
                    outFeat = QgsFeature()
                    # create the geometry as polygon from the point list
                    outGeom = QgsGeometry.fromMultiPointXY(hull).convexHull()
                    # add the geometry to the feature
                    outFeat.setGeometry(outGeom)
                    # create the attributes list: NOTE: we are using the distArea object created outside the loop to speed up
                    attrs = [value, distArea.measureArea(outGeom), distArea.measurePerimeter(outGeom)]
                    # add the attributes to the feature
                    outFeat.setAttributes(attrs)

                    
                   

                 

                    # write the feature into the QgsFeatureSink
                    sink.addFeature(outFeat, QgsFeatureSink.FastInsert)


            feedback.setProgress(int(current * total))


        

        
        self.dest_id = dest_id
        return {self.OUTPUT: dest_id}

    def postProcessAlgorithm(self, context, feedback):
        """
        PostProcessing to define the Symbology
        """
        output = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        correct = {
            '1.Bianca':('green','Josie'),
            '2.Bianca':('yellow','Bianca'),
            '3.Josie':('orange','Lula'),
            '4.Evelyn':('red','Evelyn')
            }

        categories=[]
        for animal, (color, label) in correct.items():
            sym = QgsSymbol.defaultSymbol(output.geometryType())
            sym.setColor(QColor(color))
            category = QgsRendererCategory(animal, sym, label)
            categories.append(category)

        # name the field containing the land use value:
        field = "ID"

        # build the renderer:
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # add the renderer to the layer:
        output.setRenderer(renderer)
    
        output.startEditing()

        return {self.OUTPUT: self.dest_id}

    def percpoints(self, percent, list_distances, l):
        l = (l * percent) / 100
        hull = []
        n = 1
        for k in sorted(list_distances.keys()):
            if n < l:
                points = list_distances[k].asPoint()
                hull.append(points)
                n += 1
            else:
                return hull

        return hull

    def name(self):
        return 'MCP'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Animove Algorithms'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def icon(self):
        icon_path = os.path.join(
            os.path.dirname(__file__),
            'icons',
            'mcp.png'
        )
        return QIcon(icon_path)

    def tags(self):
        return self.tr('random,mcp,animal').split(',')

    def createInstance(self):
        return AnimoveMCP()

class LayerStyler(QgsProcessingLayerPostProcessorInterface):
        print("yolo")
        def postProcessLayer (self, layer, context, feedback):
            print(layer)
           
                
