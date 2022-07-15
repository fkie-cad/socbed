# Userbehavior

## Synopsis

This package is developed as part of SOCBED.
It simulates the interaction of a user with programs and with the filesystem.
Simulated interactions include browsing, mailing and manipulating files.
The main purpose of this package is to provide legitimate and realistic log data for all these interaction.

At this stage, the userbehavior mainly works in SOCBED, but is meant to be used independently in the future.

## Requirements

The userbehavior runs with Python 3 (tested with Python 3.5).

The following packages are needed:

- For Browsing: selenium
- For Testing: pytest

## Installation

Install required packages:
```
pip install selenium pytest
```

- alternative: zip the userbehavior and use it non another machine

## Running

Running the userbehavior is only possible in SOCBED at this stage.

To run it:
```
python run.py --use-breach-setup
```

## Running the tests

Tests are written in py.test and may be run with:
```
py.test .
```
Long-running tests are may be avoided:
```
py.test -m "not(long_test)"
```

## Configuration

- should be easier and better...
- in progress....
