# foglamp-south-opcua_py
OPC UA Plugin for Foglamp based on the FreeOPCUA (Python) library.

This is a plugin that creates subscriptions to an OPC UA server and plublishes data into the Foglamp (https://dianomic.com/platform/foglamp/) platform.

Tested against:
1. DeltaV 14.3 FP1 OPC UA server (anonymous)
2. Kepserver 6.5 (anonymous and username/password)


Work to do:
* Move to asynchronous OPC UA from FreeOPCUA (https://github.com/FreeOpcUa/opcua-asyncio)
* Enable certificate support (in progress in this branch)
