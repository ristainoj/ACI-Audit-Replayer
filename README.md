# Audit Replayer

```
The goal of thi Script is to pass an APIC Audit Log in JSON or XML Format, and Re-play the same changes in the Lab.  
When you run the scipt, you can specify a number of parameters:

JRISTAIN-M-D3NK:Replay_Audits josephristaino$ python replay_audits.py --help
usage: replay_audits.py [-h] [--file FILE] [--xml] [--json] [--ip IP]
                        [--username USERNAME] [--password PASSWORD] [--https]
                        [--port PORT] [--waitTime TIME] [--step]
                        [--debug DEBUG]

optional arguments:
  -h, --help           show this help message and exit
  --file FILE          filename
  --xml                input in xml format
  --json               input in json format
  --ip IP              APIC URL
  --username USERNAME  admin username
  --password PASSWORD  admin password
  --https              Specifies whether to use HTTPS authentication
  --port PORT          port number to use for APIC communicaton
  --waitTime TIME      Time in seconds to wait between changes
  --step               Prompt For User input between each step
  --debug DEBUG        debug level
  
  The Script detects what config changes have been made and will prompt you for interfaces and domains to use to "replace" when the config is pushed.
  This way you can run the script on any fabric and use interfaces/domains from that Fabric against any Audit Log.
  ```

# Caveats:
```
  1) The APIC you are deploying to must be on the same version of code as the system where the Audits were collected.
  2) You need to allocate a VLAN pool to each domain that maps exactly to the customer, or contains all VLANS.
  
```

# Open Enhancements

```
1) Be able to wait the exact amount of time between changes as the original time it was deployed.
2) Be able to point to the location of the APIC catalog file s it can be run on a newer version that the system the Audits were collected on
```