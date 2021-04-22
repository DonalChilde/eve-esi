=============
Using the API
=============

Eve Esi Jobs is an api with a accompanying cli that intends to make accessing
Eve Online's ESI api a bit more convenient. The api provides a way to describe
a request to the ESI - an :py:class:`models.EsiJob` - that can be saved and repeated,
along with a callback framework to manipulate the completed request data. Jobs can
be collected into a :py:class:`models.EsiWorkOrder`, allowing a collection of jobs to
be completed concurrently, greatly decreasing the time required to complete the jobs. One
example use case would be downloading the complete market history for a region,
something that requires thousands of individual requests. When you consider that you may
need to do this every day, Eve Esi Jobs can save lots of time.

for example:

.. literalinclude:: /examples/script_example.py
    :language: python
