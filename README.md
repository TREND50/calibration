# Calibration tools for TREND-50

This is a collection of **Python** scripts used for the calibration of the **TREND-50** data.

**Note** that the _pre-processed_ PSD data -required for the analysis- are **not** handled by git since there are too big, i.e. ~4 GB. There are stored at Lyon in `/sps/hep/trend/calibration/data` instead.

The main scripts used for building the gains are [compute-gain.py][1] and [tabulate-gain.py][2]. An simple example of usage is provided by the [check-galactic.py][3] script.

[1]: scripts/compute-gain.py
[2]: scripts/tabulate-gain.py
[3]: scripts/check-galactic.py
