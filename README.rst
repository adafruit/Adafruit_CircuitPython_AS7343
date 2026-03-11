Introduction
============


.. image:: https://readthedocs.org/projects/adafruit-circuitpython-as7343/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/as7343/en/latest/
    :alt: Documentation Status


.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/adafruit/Adafruit_CircuitPython_AS7343/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_AS7343/actions
    :alt: Build Status


.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff

CircuitPython driver library for AS7343 14-channel Light sensor


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_
* `Register <https://github.com/adafruit/Adafruit_CircuitPython_Register>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.



Adafruit AS7343 14-Channel Light / Color Sensor Breakout - STEMMA QT / Qwiic

`Purchase one from the Adafruit shop <http://www.adafruit.com/products/6477>`_

Installing from PyPI
=====================

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-as7343/>`_.
To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-as7343

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-as7343

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .venv
    source .env/bin/activate
    pip3 install adafruit-circuitpython-as7343

Installing to a Connected CircuitPython Device with Circup
==========================================================

Make sure that you have ``circup`` installed in your Python environment.
Install it with the following command if necessary:

.. code-block:: shell

    pip3 install circup

With ``circup`` installed and your CircuitPython device connected use the
following command to install:

.. code-block:: shell

    circup install adafruit_as7343

Or the following command to update an existing version:

.. code-block:: shell

    circup update

Usage Example
=============

.. code-block:: python

    import time

    import board

    from adafruit_as7343 import AS7343

    i2c = board.I2C()
    sensor = AS7343(i2c)

    CHANNEL_LABELS = [
        "FZ (450nm blue)",
        "FY (555nm yellow-green)",
        "FXL (600nm orange)",
        "NIR (855nm near-IR)",
        "VIS_TL_0 (clear top-left, cycle 1)",
        "VIS_BR_0 (clear btm-right, cycle 1)",
        "F2 (425nm violet-blue)",
        "F3 (475nm blue-cyan)",
        "F4 (515nm green)",
        "F6 (640nm red)",
        "VIS_TL_1 (clear top-left, cycle 2)",
        "VIS_BR_1 (clear btm-right, cycle 2)",
        "F1 (405nm violet)",
        "F7 (690nm deep red)",
        "F8 (745nm near-IR edge)",
        "F5 (550nm green-yellow)",
        "VIS_TL_2 (clear top-left, cycle 3)",
        "VIS_BR_2 (clear btm-right, cycle 3)",
    ]

    while True:
        readings = sensor.all_channels
        print("--- AS7343 Channel Readings ---")
        for label, value in zip(CHANNEL_LABELS, readings):
            print(f"  {label}: {value}")
        print()
        time.sleep(1)


Documentation
=============
API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/as7343/en/latest/>`_.

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_AS7343/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
