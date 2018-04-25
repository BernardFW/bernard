BERNARD
=======

**Version 0.2**

|Build Status|

Building *instant services* (or chatbots) is a brand new craft. BERNARD
is here to bring it up to speed for the professional world.

-  Take advantage of each platform's specificities (Facebook, Telegram,
   ...)
-  Connect your existing business API
-  Translate and decline your texts
-  Extensible to any platform, without merging to upstream

Get started!
============

This documentation will bring you methodology, concepts and patterns to
build bots as well as hands-on experience with the code of a bot.

-  **`Get Started <./doc/get-started/readme.md>`__** course and tutorial
-  **`Table of contents <./doc/readme.md>`__** of all topics in
   documentation

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
-  Imports are normalized by the ``make imports`` command
-  No undocumented code gets merged
-  Code bringing test coverage down or breaking tests doesn't get merged

Testing
-------

Use ``py.test``. Node for later: document this part a bit better.

.. |Build Status| image:: https://travis-ci.org/BernardFW/bernard.svg?branch=develop
   :target: https://travis-ci.org/BernardFW/bernard
