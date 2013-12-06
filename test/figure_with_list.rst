Simple columns
--------------

.. beamer-simplecolumns::
    :width: 0.95

    .. image:: plot.png
       :width: 130%


    * bullet 1
    * bullet 2
    * bullet 3


Explicit columns
----------------

.. beamer-columnset::
    :width: 0.95

    .. beamer-column::
        :width: 0.75

        .. image:: plot.png


    .. beamer-column::

        * bullet 1
    	* bullet 2
    	* bullet 3



A slide without columns
-----------------------

Just to make sure our "columnization" isn't persistent, this should show up
up as a plain normal slide.
