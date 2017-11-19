Health Checks
=============

When the framework starts, it performs a health check on itself to detect
possible bugs or misconfigurations. Here is the list of error codes and the
explanation associated.

## 00001 - Missing fail method

When you use the context's `@inject()` decorator with a non-empty `require` 
list then it might happen that the required context entry goes missing. In this
case, your state is required to have a fail method which will be called in
stead of the handler. The default name of this method is `missing_context` but
you can configure it using the `fail` parameter.

## 00002 - Duplicate platform

This happens when the `PLATFORM` configuration variable contains the same
platform twice. You need to review your configuration and remove duplicate
platforms.

## 00003 - Non-existent platform

The `class` specified in the `PLATFORM` configuration cannot be found. You need
to specify a platform that exist or to fix your Python PATH.

## 00004 - Missing class name

In the `PLATFORMS` list, you need to specify a class name.

## 00005 - Incorrect config

Something is missing in the configuration. The error message should give you
information about what exactly is missing.
