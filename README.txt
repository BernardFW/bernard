BERNARD
=======

|Build Status|

Create powerful and flexible bots using BERNARD. It comes
batteries-included and with strong opinions. You'll be able to:

-  Represent conversations as finite-state machines
-  Multi-platform (Facebook Messenger, WeChat, VK, Line, Twilio, ...)
-  Flexible translation system. Handles language, plurals, gender and
   anything you'd like
-  Run-time analysis through logging

BERNARD stands for "Bot Engine Responding Naturally At Requests
Detection".

Get started
===========

Please go to the `get started <doc/get_started.md>`__ section!

Licensing
=========

There is a dual licencing scheme here:

-  By default, AGPL v3+
-  If your project is not compatible with the AGPL, please contact
   *remy.sanchez@with-madrid.com*.

Contribution
============

Contribution is of course welcome, although there is a few rules to
respect for the well-being of the project.

Governance
----------

Please do not hesitate to communicate through GitHub issues before
committing to a large contribution: the team of the project has plans
and priorities, so if you end up going against those it will be hard to
merge your code.

Coding Rules
------------

Coding rules are very, very important. There is not too many yet:

-  PEP 8
-  No undocumented code gets merged
-  Code bringing test coverage down or breaking tests doesn't get merged

Testing
-------

Use ``py.test``. Node for later: document this part a bit better.

Vision
======

The vision of the framework API was established in the `the vision
doc <doc/vision.md>`__. This document is the basis of any development
going on as it tries to bring consistency to all the different concepts
and problems encountered in bot making.

.. |Build Status| image:: https://travis-ci.org/BernardFW/bernard.svg?branch=develop
   :target: https://travis-ci.org/BernardFW/bernard
