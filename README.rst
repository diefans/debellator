.. container:: bagdes

    .. image:: https://travis-ci.org/diefans/implant.svg?branch=master
       :target: https://travis-ci.org/diefans/implant
       :align: right

    .. image:: https://img.shields.io/pypi/pyversions/implant.svg
       :target: https://pypi.org/project/implant/
       :alt: PyPI - Python Version

    .. image:: https://img.shields.io/pypi/v/implant.svg
       :target: https://pypi.org/project/implant/
       :alt: PyPI

    .. image:: https://img.shields.io/readthedocs/implant.svg
       :target: http://docs.implant.codes
       :alt: Read the Docs

    .. image:: https://codecov.io/gh/diefans/implant/branch/master/graph/badge.svg
       :target: https://codecov.io/gh/diefans/implant

----

.. image:: implant.png
   :alt: implant
   :align: left


implant
**********

A proof-of-concept for asynchronous adhoc remote procedure calls in Python.

This is work in progress and serves basically as an exercise.


.. inclusion-marker-do-not-remove


Features
========

- Python >= 3.5 asyncio

- adhoc transferable remote procedures

- remote part of a `implant.core.Command` may reside in a separate module

- a `implant.core.Command` specific `implant.core.Channel`
  enables arbitrary protocols between local and remote side

- events

- quite small core

- tests


Limitations
===========

- Python >= 3.5

- only pure Python modules are supported for remote import, if no venv is used

- `implant.core.Command` s must reside in a module other then `__main__`

- at the moment sudo must not ask for password



Example
=======


General application
-------------------

.. code:: python

    import asyncio
    import pathlib

    from implant import core, connect, commands


    async def remote_tasks():
        # create a connector for a python process
        connector = connect.Lxd(
            container='zesty',
            hostname='localhost'
        )
        connector_args = {
            'python_bin': pathlib.Path('/usr/bin/python3')
        }
        # connect to a remote python process
        remote = await connector.launch(**connector_args)

        # start remote communication tasks
        com_remote = asyncio.ensure_future(remote.communicate())
        try:
            # execute command
            cmd = commands.SystemLoad()
            result = await remote.execute(cmd)

            print("Remote system load:", result)

        finally:
            # stop communication tasks
            com_remote.cancel()
            await com_remote


    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(remote_tasks())
        loop.close()


An example Echo Command
-----------------------

.. code:: python

    import logging
    import os

    from implant import core


    log = logging.getLogger(__name__)


    class Echo(core.Command):

        """Demonstrate the basic command API."""

        async def local(self, context):
            """The local side of the RPC.

               :param context: :py:obj:`implant.core.DispatchLocalContext`
            """
            # custom protocol
            # first: send
            await context.channel.send_iteration("send to remote")

            # second: receive
            from_remote = []
            async for x in context.channel:
                from_remote.append(x)
            log.debug("************ receiving from remote: %s", from_remote)

            # third: wait for remote to finish and return result
            remote_result = await context.remote_future

            result = {
                'from_remote': ''.join(from_remote),
            }
            result.update(remote_result)
            return result

        async def remote(self, context):
            """The remote side of the RPC.

               :param context: :py:obj:`implant.core.DispatchRemoteContext`
            """
            # first: receive
            from_local = []
            async for x in context.channel:
                from_local.append(x)
            log.debug("************ receiving from local: %s", from_local)

            # second: send
            await context.channel.send_iteration("send to local")

            # third: return result
            return {
                'from_local': ''.join(from_local),
                'remote_self': self,
                'pid': os.getpid()
            }


Internals
=========

::

    master <-----------------------------------------> remote
                                |
                           stdin/stdout
                                |
                              chunks
                                |
                             channels
                                |
        --> send ---> |                   |  --> queue -->
                      | module:class/fqin |
        <-- queue <-- |                   |  <--- send <--

