AniMove algorithms for QGIS
---------------------------
QGIS provides a processing environment that can be used to call native and third
party algorithms, making your spatial analysis tasks more productive and easy to
accomplish.

AniMove plugin implements, as a processing submodule, kernel analyses with the
following algs:

* **href**: the *reference* bandwidth is used in the estimation.
* **LSCV (The Least Square Cross Validation)**: the *LSCV* bandwidth is used in
  the estimation.
* **Scott's Rule of Thumb**: the Scott's rule of thumb is used for bandwidth
  estimation.
* **Silverman's Rule of Thumb**: the Silverman's rule of thumb is used for
  bandwidth estimation.
* kernel with adjusted *h*

Utilization distribution and contour lines are produced, and area of the contour
polygons are calculated.

Additionally, restricted Minimum Convex Polygons (MCP) are implemented, as:

* MCP calculation of the smallest convex polygon enclosing all the relocations
  of the animal, excluding an user-selected percentage of locations furthest
  from a centre.

**NOTE**: some of the bandwidth methods are only available with *statsmodels*
(LSCV, maximum-likelihood cross-validation).

* A new tool called "Random path" that allows to randomize paths (lines) with many options:
keep angles, randomize angles (range as user choice), randomize starting points,
keep starting points, use a point layer for starting points, check if the random
path crosses features of a specified line/polygon layer.


Support
-------

Part of the [AniMove project](http://www.faunalia.it/animove) supported by
Faunalia.

The plugin was developed by:

* Jorge Arévalo ([geomati.co](http://geomati.co))
* Francesco Boccacci
* Víctor González ([geomati.co](http://geomati.co))
* Alexander Bruy for Faunalia ([faunalia.eu](http://www.faunalia.eu))

and financially supported by:

* Marco Zaccaroni - Department of Biology, University of Firenze
* António Mira
* Dimitris Poursanidis
* Giovanni Manghi
* Stefano Anile
* Wildlife Conservation Research Unit (WildCRU), University of Oxford
* Julia Hazel
* Prof. António Mira (University of Évora, Portugal, Unidade de Biologia da
  Conservação)
* Dr. Rosana Peixoto PhD


Porting
-------
The porting of the plugin AniMove to QGIS 3 has been financially
supported by Ente Monti Cimini - Riserva Naturale Lago di Vico within the
project "LIFE18 NAT/IT/000720“ – Lanner*.