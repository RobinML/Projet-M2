# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Animove
                                 A QGIS plugin
 AniMove for QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-19
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
__date__ = '2021-07-19'
__copyright__ = '(C) 2021 by Matteo Ghetta (Faunalia)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsDistanceArea,
                       QgsGeometry,
                       QgsFeature,
                       QgsProcessingException,
                       QgsFeatureRequest,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)
import random
import math
import codecs
import os


class AnimoveRandomHR(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # INPUTS
    HR_LAYER = 'HR_LAYER'
    STUDY_LAYER = 'STUDY_LAYER'
    ITERATIONS = 'ITERATIONS'
    
    # OUTPUTS
    RANDOM_HR = 'RANDOM_HR'
    HTML = 'HTML'
    RAW_DATA = 'RAW_DATA'
    SUMMARY_DATA = 'SUMMARY_DATA'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        ### INPUTS ###

        # input HR polygon layer
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.HR_LAYER,
                description=self.tr('HR layer'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )

        # input study polygon layer
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.STUDY_LAYER,
                description=self.tr('Study layer'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )


        # iteration number
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.ITERATIONS,
                description=self.tr('Number of iterations'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=10,
                minValue=1,
                maxValue=999

            )
        )


        # OUTPUTS ###

        # final sink of Random HR
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.RANDOM_HR,
                description=self.tr('Random HR')
            )
        )

        # HTML file of random hr results
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.HTML,
                description=self.tr('Random HR results'),
                fileFilter=self.tr('HTML files (*.html')
                
            )
        )

        # RAW DATA file of random hr results
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.RAW_DATA,
                description=self.tr('Raw Output'),
                fileFilter=self.tr('HTML files (*.html')
            )
        )

        # SUMMARY DATA file of random hr results
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.SUMMARY_DATA,
                description=self.tr('Output summary'),
                fileFilter=self.tr('HTML files (*.html')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # get reference of the hr layer
        hrLayer = self.parameterAsSource(
            parameters, 
            self.HR_LAYER, 
            context
        )

        # get reference of the study layer
        studyLayer = self.parameterAsSource(
            parameters,
            self.STUDY_LAYER,
            context
        )

        # get the reference of iterations number
        iterations = self.parameterAsInt(
            parameters,
            self.ITERATIONS,
            context
        )

        # html file output of random hr
        toolLog = self.parameterAsFileOutput(
            parameters,
            self.HTML,
            context
        )

        # html file output of raw data
        rawFile = self.parameterAsFileOutput(
            parameters,
            self.RAW_DATA,
            context
        )

        # html file output of summary data
        sumFile = self.parameterAsFileOutput(
            parameters,
            self.SUMMARY_DATA,
            context
        )

        # raise exception if the study layer has a feature count different from 1
        if studyLayer.featureCount() != 1:
            raise QgsProcessingException(self.tr('The study area layer should contain exactly one polygon or '
                'multipolygon.'))
        
        # loop into the vector layer and get the difference polygon
        if studyLayer.getFeatures(QgsFeatureRequest().setFilterFid(0)).isValid():
            raise QgsProcessingException(self.tr('Problem layer not valid.'))

        f = QgsFeature()
        studyLayer.getFeatures(QgsFeatureRequest().setFilterFid(0)).nextFeature(f)
        # get the geom bbox
        rect = f.geometry().boundingBox()
        # get the difference between the bbox and the geometry
        outside = QgsGeometry().fromRect(rect).difference(f.geometry())


        # create a materialized copy of the input hr layer
        self.layer = hrLayer.materialize(QgsFeatureRequest())
        provider = self.layer.dataProvider()

        # create the QgsDistanceArea object to measure the geometries information
        da = QgsDistanceArea()
        da.setSourceCrs(hrLayer.sourceCrs(), context.transformContext())
        da.setEllipsoid(context.project().ellipsoid())


        # list of the hrLayer areas
        areas = []

        for i in self.layer.getFeatures():
            # area measure in meters
            area_measure = da.measureArea(i.geometry())
            areas.append(area_measure)
        

        # analyze source overlaps
        self.overlaps = []
        self.overlapsTotal = []

        self.overlaps += self._calculateOverlaps(feedback, context)
        self.overlapsTotal += [self._sum2d(self.overlaps[0])]

        # start write the html output string
        html = '<table border="1">'
        html += '<tr><td colspan="3">'
        html += 'Number of homeranges: %d' % len(areas)
        html += '</td></tr>'
        html += '<tr><td colspan="3">'
        html += 'Total area of the homeranges: %.3f' % sum(areas)
        html += '</td></tr>'
        html += '<tr><td></td><td>total overlap area</td><td>SD</td></tr>'
        html += '<tr><td>observed</td><td>%.3f</td><td>n/a</td></tr>' % self.overlapsTotal[0]

        
        total = 100 / iterations
        total_features = 100 / self.layer.featureCount() if self.layer else 0

        feedback.pushInfo(self.tr('Depending on the total features and on the number of iterations, the calculations can take a long time!\n'))
        feedback.pushInfo(self.tr(f'The layer has {self.layer.featureCount()} features and you choose {iterations} iterations\n'))

        for current in range(iterations):
            
            if feedback.isCanceled():
                break
            
            for current_feature, f in enumerate(self.layer.getFeatures()):

                if feedback.isCanceled():
                    break

                feedback.setProgressText(self.tr(f"Feature {f.id()} of the {current+1} iteration"))

                sticksOut = True
                while sticksOut:
                    geom = self._rotate(f.geometry(), feedback, context)
                    tries = 0
                    while sticksOut and tries < 50:

                        if feedback.isCanceled():
                            break

                        geom = self._move(geom, rect)
                        sticksOut = outside.intersects(geom)
                        tries+=1
                provider.changeGeometryValues({f.id(): geom})
                feedback.setProgress(int(current_feature * total_features))

            self.overlaps += self._calculateOverlaps(feedback, context)
            overlap = self._sum2d(self.overlaps[len(self.overlaps) - 1])
            self.overlapsTotal += [overlap]

            html += '<tr><td>iteration %d</td><td>%.3f</td><td>n/a</td></tr>' % (current + 1, overlap)

            feedback.setProgress(int(current * total))


        (mean, sd) = self._calculateStats(feedback, context)

        html += '<tr><td>mean</td><td>%.3f</td><td>%.3f</td></tr>' % (mean, sd)
        html += '</table>'
        html += '<h1>Result</h1>'

        dist = self.overlapsTotal[0] - mean
        if dist > 0:
            t = 'more'
        else:
            t = 'less'

        html += '<p>Distance between the observed and randomized value is: %0.3f (the observed one is %s).</p>' % (dist, t)
        html += '<p>The standard deviation is: %.3f.</p>' % sd
        html += '<p>The last iteration result has been saved.</p>'


        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.RANDOM_HR,
            context,
            fields,
            QgsWkbTypes.MultiPolygon, # polygon layer
            hrLayer.sourceCrs()  # same CRS of the input layer
        )


        total = 100 / self.layer.featureCount() if self.layer else 0

        for current, f in enumerate(self.layer.getFeatures()):
                
            feature = QgsFeature()
            feature.setFields(fields)
            feature.setGeometry(f.geometry())
            feature.setAttribute('id', f.id())

            sink.addFeature(feature, QgsFeatureSink.FastInsert)

        results = {self.RANDOM_HR: dest_id}


        results[self.RAW_DATA] = self.writeRaw(rawFile, hrLayer, studyLayer, areas, feedback, context)
        results[self.SUMMARY_DATA] = self.writeSummary(sumFile, hrLayer, studyLayer, feedback, context)

        return results


    def _calculateOverlaps(self, feedback, context):

        # collect the geometries
        polygons = []
        for f in self.layer.getFeatures():
            geom = QgsGeometry(f.geometry())
            polygons.append(geom)

        # set the QgsDistanceArea
        result = []
        da = QgsDistanceArea()
        da.setSourceCrs(self.layer.crs(), context.transformContext())
        da.setEllipsoid(context.project().ellipsoid())
        
        # iterate in the polygons (QgsGeometry) and measure the area of the
        # intersection between each polygon of the same layer
        for i, f in enumerate(polygons):
            tmp = []
            for j in range(i + 1, len(polygons)):
                # only if there is intersection between layers
                if polygons[i].intersects(polygons[j]):
                    # measure the area
                    overlap = da.measureArea(polygons[i].intersection(polygons[j]))
                # if tehre is not intersection
                else:
                    overlap = 0.0
                tmp.append(overlap)
            result += [tmp]
        return [result]


    def _sum2d(self, data):
        k = 0
        for i in data:
            for j in i:
                k += j
        return k

    def _rotate(self, geom, feedback, context):
        # randomize the angle
        angle = random.uniform(0, 2 * math.pi)
        sina = math.sin(angle)
        cosa = math.cos(angle)
        i = 0
        # create unique dict of verticles because of overlapping the
        # first and the last one
        unique = dict()
        vertex = geom.vertexAt(i)
        # go on until the vertex is not an empty QgsPoint
        while not vertex.isEmpty():
            
            if feedback.isCanceled():
                break

            unique[i] = vertex
            vertex = geom.vertexAt(i)
            i += 1

        for key in unique.keys():
            vertex = unique[key]
            x = cosa * vertex.x() - sina * vertex.y()
            y = sina * vertex.x() + cosa * vertex.y()
            geom.moveVertex(x, y, key)

        return geom

    def _move(self, geom, rect):
        bbox = geom.boundingBox()
        # compute allowed movement range
        dxMin = rect.xMinimum() - bbox.xMinimum()
        dxMax = rect.xMaximum() - bbox.xMaximum()
        dyMin = rect.yMinimum() - bbox.yMinimum()
        dyMax = rect.yMaximum() - bbox.yMaximum()
        # randomize dx and dy
        dx = random.uniform(dxMin, dxMax)
        dy = random.uniform(dyMin, dyMax)
        # move
        geom.translate(dx, dy)
        return geom

    def _calculateStats(self, feedback, context):
        data = self.overlapsTotal[1:]
        mean = sum(data) / len(data)
        sd = 0
        for i in data:
            sd += (i - mean) * (i - mean)
        if len(data) > 1:
          sd = math.sqrt(sd / (len(data) - 1))
        else:
          sd = 0
        return (mean, sd)

    def writeSummary(self, fileName, hrLayer, studyLayer, feedback, context):

        with codecs.open(fileName, 'w', encoding='utf-8') as f:
            f.write('<html><head>')
            f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" /></head><body>')

            f.write('<h1>QGIS Random Home Range summary</h1>\n')
            f.write(f'<p>Frame layer: {studyLayer.sourceName()}</p>\n')
            f.write(f'<p>Home ranges layer: {hrLayer.sourceName()}</p>\n')
            f.write(f'<p>Number of the home ranges: {hrLayer.featureCount()}</p>\n')
            f.write(f'<p>Number of iterations: {len(self.overlaps) - 1}</p>\n\n' )
            f.write(f'<p>observed overlaps {self.overlapsTotal[0]: .2f} squared meters<p>\n')
            for i in range(1, len(self.overlapsTotal)):
                f.write(f'<p>iteration {i}: {str(self.overlapsTotal[i])} squared meters</p>\n')

            (mean, sd) = self._calculateStats(feedback, context)
            f.write(f'<p>mean: {mean: .2f} squared meters</p>\n')
            f.write(f'<p>standard deviation: {sd: .2f} squared meters</p>\n')
            f.write(f'<p>observed-randomized: {(self.overlapsTotal[0] - mean): .2f} squared meters</p>\n\n')
            #f.write(f'<p>observed/randomized: {(self.overlapsTotal[0] / mean): .2f} squared meters</p>\n\n')

            f.write('</body></html>')
        
        return fileName
    

    def writeRaw(self, fileName, hrLayer, studyLayer, areas, feedback, context):

        with codecs.open(fileName, 'w', encoding='utf-8') as f:
            f.write('<html><head>')
            f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" /></head><body>')

            f.write(f'<h1>QGIS Random Home Range summary</h1>\n')
            f.write(f'<p>Frame layer: {studyLayer.sourceName()}</p>\n')
            f.write(f'<p>Home ranges layer: {hrLayer.sourceName()}</p>\n')
            f.write(f'<p>Number of the home ranges: {studyLayer.featureCount()}</p>\n')
            f.write(f'<p>Number of iterations: {len(self.overlaps) - 1}</p>\n\n')
            f.write(f'<p>Note: The first column contains the home range area\n\n')
            for i, ii in enumerate(self.overlaps):
                if i == 0:
                    f.write('<p>Observed data:</p>\n')
                else:
                    f.write(f'<p>Iteration {i}:</p>\n')

                for j, jj in enumerate(self.overlaps[i]):
                    text = str(areas[j]) + ';'
                    for k in range(len(self.overlaps[i]) - len(self.overlaps[i][j])):
                        text += ';'

                    for k in range(len(self.overlaps[i][j])):
                        val = self.overlaps[i][j][k]
                        text += str(val) + ';'

                    text = text[:len(text) - 1] + '\n'
                    f.write(text)

                f.write('\n')
            f.write('</body></html>')
        
        return fileName

    def name(self):
        return 'Random HR'

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
        return self.tr('random,home range,animal').split(',')

    def createInstance(self):
        return AnimoveRandomHR()
