# Audit Replayer

```
The goal of thi Script is to pass an APIC Audit Log in JSON or XML Format, and Re-play the same changes in the Lab.  
When you run the scipt, you can specify a number of parameters:

JRISTAIN-M-D3NK:Replay_Audits josephristaino$ python replay_audits.py --help
usage: replay_audits.py [-h] [--file FILE] [--xml] [--json] [--ip IP]
                        [--username USERNAME] [--password PASSWORD] [--https]
                        [--port PORT] [--catalog CATALOG]
                        [--startTime STARTTIME] [--endTime ENDTIME]
                        [--waitTime TIME] [--step] [--debug DEBUG]

optional arguments:
  -h, --help            show this help message and exit
  --file FILE           filename
  --xml                 input in xml format
  --json                input in json format
  --ip IP               APIC URL
  --username USERNAME   admin username
  --password PASSWORD   admin password
  --https               Specifies whether to use HTTPS authentication
  --port PORT           port number to use for APIC communicaton
  --catalog CATALOG     manually specify MESSAGE-CATALOG.txt from version of
                        code audits were pulled from
  --startTime STARTTIME
                        Time to begin deploying Audits. Must be in the
                        following Format: YYYY-MM-DDTHH:MM:SS
  --endTime ENDTIME     Time to Stop deploying Audits. Must be in the
                        following Format: YYYY-MM-DDTHH:MM:SS
  --waitTime TIME       Time in seconds to wait between changes
  --step                Prompt For User input between each step
  --debug DEBUG         debug level
  --tenant TENANT       Tenant You Wish to Replay Audits For
  --remap               Set if you would like to remap objects to new ones
  
  The Script detects what config changes have been made and will prompt you for interfaces and domains to use to "replace" when the config is pushed.
  This way you can run the script on any fabric and use interfaces/domains from that Fabric against any Audit Log.
  
  The original idea was to take audits and replay them in "any" lab environment.  In order to accomplish this, some objects need to be "re-mapped" to objects that exist in the setup you are deploying them on.  An example of this is a static path binding.  The leaf node and interface where the audit was done may not exist in the lab you are deploying.  The "--remap" argument should be used in this case to be prompted for input for any objects that will need remapping.  By default, it will try and push the audit as is.
  
  
  ```

# Caveats:
```
  1) The APIC you are deploying to must be on the same version of code as the system where the Audits were collected.
  2) You need to allocate a VLAN pool to each domain that maps exactly to the customer, or contains all VLANS.
  
```

# Open Enhancements

```
1) Be able to wait the exact amount of time between changes as the original time it was deployed.
```
