# foglamp-south-opcua_py
OPC UA Plugin for Foglamp based on the FreeOPCUA (Python) library.

This is a plugin that creates subscriptions to an OPC UA server and plublishes data into the Foglamp (https://dianomic.com/platform/foglamp/) platform.

Tested against:
1. DeltaV 14.3 FP1 OPC UA server (anonymous and username/password)
2. Kepserver 6.5 (anonymous and username/password)
3. Open62541 test server (anonymous)

# Usage
1. Download an OPC UA client such as Prosys (https://www.prosysopc.com/products/opc-ua-browser/) or UaExpert (https://www.unified-automation.com/products/development-tools/uaexpert.html) 
2. Find the URL/endpoint of the OPC UA server, for example: opc.tcp://historian.local:9409/DvOPC
3. Using the client, log into the server and note the required security level. Plugin currently supports anonymous logins and ones with username/password. Certificate authentication not currently implemented.
4. Browse through the namespace and find the tags to monitor. Record their names, which should include the namespace (ns=). Examples include ns=2;s=0:FIT-321.CV or ns=1;i=1234.
5. In FogLamp, create a new south opcua_py service and enter information noted above. This will create subscriptions to these tags.
6. Optional: Use an asset filter (https://github.com/foglamp/foglamp-filter-asset) to rename the OPC UA tags to more readable values, if desired. Example:
{"asset_name": "ns=2;s=0:FIT-321.CV", "action": "rename", "new_asset_name": "FIT-321"}

Work to do:
* Move to asynchronous OPC UA from FreeOPCUA (https://github.com/FreeOpcUa/opcua-asyncio)
* Enable certificate support
