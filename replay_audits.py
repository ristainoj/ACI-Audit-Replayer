__author__ = 'josephristaino'

import os, sys, logging, getpass, re, json, time, requests
from acisession import Session
from lxml import html
import lxml.etree as etree
import dateutil
import dateutil.parser


MINIMUM_POD  = 1
MAXIMUM_POD  = 16
MINIMUM_NODE = 100
MAXIMUM_NODE = 5000
MINIMUM_PORT = 1
MAXIMUM_PORT = 96

intTypes = {
        1 : "Access Port",
        2 : "Port-Channel / VPC"
    }
"""
domTypes = {
        1 : "VMM Domain",
        2 : "Physical Domain"
    }
"""
reMapObjects = [
        "rsdomAtt-[uni/phy",
        "rsdomAtt-[uni/vmmp-VMware",
        "rsl3DomAtt",
        "rspathAtt",
        "rspathL3OutAtt",
        "rsnodeL3OutAtt"
    ]

def parse_timestamp(ts_str):
    """ return float unix timestamp for timestamp string 
        return None on error
    """
    try:
        dt = dateutil.parser.parse(ts_str, yearfirst=True, fuzzy=True)
        return (time.mktime(dt.timetuple()) + dt.microsecond/1000000.0)
    except ValueError as e: 
        return None

def getVMMUserInfo(session):

    vmmDomDNList = []

    #########################
    # GET vmmDomP from APIC #
    #########################
    vmmDomUrl = "/api/node/class/vmmDomP.json"
    vmmDomResp = session.get(vmmDomUrl)
    vmmDomJS = vmmDomResp.json()

    vmmDomCount = vmmDomJS['totalCount']
    for i in range(0, int(vmmDomCount)):
        vmmDomDN = vmmDomJS["imdata"][i]["vmmDomP"]["attributes"]["dn"]
        vmmDomDNList.append(vmmDomDN)

    # Display vmmDomP info to User
    for i, value in enumerate(sorted(vmmDomDNList)):
        print "[%s]: %s" % (i+1, value)
    print "\n"

    vmmDomChoice = None
    while vmmDomChoice is None:
        vmmDomChoice = raw_input("Which Type of VMM Domain Would You Like to Use for EPG Replacement?     :")
        try:
            vmmDomChoice = int(vmmDomChoice)
            if vmmDomChoice < 1 or vmmDomChoice >len(vmmDomDNList): raise ValueError("")
        except ValueError as e:
                print "Please select a value between 1 and %s" % len(vmmDomDNList)
                vmmDomChoice = None

    for i, value in enumerate(sorted(vmmDomDNList)):
        if vmmDomChoice-1 == i:
            vmmDom = value
    print "\n"
    print 'You have chosen "%s"\n' % vmmDom
    return vmmDom

def getPhyUserInfo(session):

    polGrpDNList = []
    bundleDNList = []
    portDNList   = []
    phyDomDNList = []

    ##########################
    # GET physDomP from APIC #
    ##########################
    phyDomUrl = "/api/node/class/physDomP.json"
    phyDomResp = session.get(phyDomUrl)
    phyDomJS = phyDomResp.json()

    # Display physDomP info to User
    phyDomCount = phyDomJS['totalCount']
    for i in range(0, int(phyDomCount)):
        phyDomDN = phyDomJS["imdata"][i]["physDomP"]["attributes"]["dn"]
        phyDomDNList.append(phyDomDN)

    # Display physDomP info to User
    phyDomDNList = sorted(phyDomDNList)
    for i, value in enumerate(sorted(phyDomDNList)):
        print "[%s]: %s" % (i+1, value)
    print "\n"

    phyDomChoice = None
    while phyDomChoice is None:
        phyDomChoice = raw_input("Which Type of Physical Domain Would You Like to Use for EPG Replacement?:")
        try:
            phyDomChoice = int(phyDomChoice)
            if phyDomChoice < 1 or phyDomChoice >len(phyDomDNList): raise ValueError("")
        except ValueError as e:
                print "Please select a value between 1 and %s" % len(phyDomDNList)
                phyDomChoice = None

    phyDom = phyDomDNList[phyDomChoice-1]

    print "\n"
    print 'You have chosen "%s"\n' % phyDom

    #################################
    # GET infraAccBaseGrp from APIC #
    #################################
    polGrpUrl = "/api/node/class/infraAccBaseGrp.json"
    polGrpResp = session.get(polGrpUrl)
    PolGrpJS = polGrpResp.json()

    # Display infraAccBaseGrp info to User
    for key, value in intTypes.iteritems():
        print "[" + str(key) + "]" + value
    print "\n"

    polGrpType = None
    while polGrpType is None:
        polGrpType = raw_input("Which Type of Interface Would You Like to Use for EPG Replacement?        :")
        if len(polGrpType) == 0 or polGrpType not in str(intTypes):
            print "Please select a valid option"
            polGrpType = None
        elif polGrpType == "1":
            polGrpType = "infraAccPortGrp"
        elif polGrpType == "2":
            polGrpType = "infraAccBndlGrp"

    print "\n"

    if polGrpType == "infraAccBndlGrp":
        polGrpCount = PolGrpJS['totalCount']
        for i in range(0, int(polGrpCount)):
            if polGrpType in PolGrpJS["imdata"][i]:
                polGrpDN = PolGrpJS["imdata"][i][polGrpType]["attributes"]["dn"]
                polGrpDNList.append(polGrpDN)

        for i, value in enumerate(sorted(polGrpDNList)):
            print "[%s]: %s" % (i+1, value)
        print "\n"

        polGrpChoice = None
        while polGrpChoice is None:
            polGrpChoice = raw_input("Which Policy Would You Like to Use for EPG Replacement?             :")
            try:
                polGrpChoice = int(polGrpChoice)
                if polGrpChoice < 1 or polGrpChoice >len(polGrpDNList): raise ValueError("")
            except ValueError as e:
                    print "Please select a value between 1 and %s" % len(polGrpDNList)
                    polGrpChoice = None

        for i, value in enumerate(sorted(polGrpDNList)):
            if polGrpChoice-1 == i:
                polGroup = value
        print "\n"
        print 'You have chosen "%s"' % polGroup

        r1 =re.search("^uni\/infra\/funcprof\/accbundle-(?P<polGrp>.*)", polGroup)

    ##############################
    # GET fabricPathEp from APIC #
    ##############################
    pathEpUrl = "/api/node/class/fabricPathEp.json"
    pathEpResp = session.get(pathEpUrl)
    pathEpJS = pathEpResp.json()


    pathEpCount = pathEpJS['totalCount']
    for i in range(0, int(pathEpCount)):
        if polGrpType == "infraAccBndlGrp":
            if r1.group("polGrp") in pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]:
                bundleDN = pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]
                bundleDNList.append(bundleDN)
        else:
            if "/pathep-[eth" in pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]:
                portDN = pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]
                portDNList.append(portDN)

    if polGrpType == "infraAccBndlGrp":
        for i,value in enumerate(sorted(bundleDNList)):
            print "[%s]: %s" % (i+1, value)
        print "\n"

        portChoice = None
        while portChoice is None:
            portChoice = raw_input("Which Static Path Would You Like to Use for EPG Replacement?          :")
            try:
                portChoice = int(portChoice)
                if portChoice < 1 or portChoice >len(bundleDNList): raise ValueError("")
            except ValueError as e:
                print "Please select a value between 1 and %s" % len(bundleDNList)
                portChoice = None

        for i, value in enumerate(sorted(bundleDNList)):
            if portChoice-1 == i:
                port = value

        print "\n"
        print 'You have chosen "%s"\n' % port

        return phyDom, port
    else:
        # Get POD
        podChoice = None
        while podChoice is None:
            podChoice = raw_input("Which Pod Will The Leaf Be Located? [%s-%s]                            :" % (MINIMUM_POD, MAXIMUM_POD))
            try:
                podChoice = int(podChoice)
                if podChoice > MAXIMUM_POD or podChoice < MINIMUM_POD: raise ValueError("")
            except ValueError as e:
                print "Pod ID must be between %s and %s" % (MINIMUM_POD, MAXIMUM_POD)
                podChoice = None

        #Get Leaf
        leafChoice = None
        while leafChoice is None:
            leafChoice = raw_input("Which Leaf will the port be Deployed?                                 :")
            try:
                leafChoice = int(leafChoice)
                if leafChoice > MAXIMUM_NODE or leafChoice < MINIMUM_NODE: raise ValueError("")
            except ValueError as e:
                print "Leaf ID must be between %s and %s" % (MINIMUM_NODE, MAXIMUM_NODE)
                leafChoice = None

        #Get Port
        portChoice = None
        while portChoice is None:
            portChoice = raw_input("Which Port Would You Like to Use for Replacement?                     :")
            try:
                portChoice = int(portChoice)
                if portChoice > MAXIMUM_PORT or portChoice < MINIMUM_PORT: raise ValueError("")
            except ValueError as e:
                print "Port ID must be between %s and %s" % (MINIMUM_PORT, MAXIMUM_PORT)
                portChoice = None

        port = "topology/pod-" + str(podChoice) + "/paths-" + str(leafChoice) + "/pathep-[eth1/" + str(portChoice) + "]"
        if port in portDNList:
            print 'You have chosen "%s"\n' % port
        else:
            print "unable to find port in Fabric"
            sys.exit()

        return phyDom, port

def getL3UserInfo(session, l3If=False, l3PC=False, l3VPC=False):

    l3DomDNList  = []

    ###########################
    # GET l3extDomP from APIC #
    ###########################
    l3DomUrl = "/api/node/class/l3extDomP.json"
    l3DomResp = session.get(l3DomUrl)
    l3DomJS = l3DomResp.json()

    # Display physDomP info to User
    l3DomCount = l3DomJS['totalCount']
    for i in range(0, int(l3DomCount)):
        l3DomDN = l3DomJS["imdata"][i]["l3extDomP"]["attributes"]["dn"]
        l3DomDNList.append(l3DomDN)

    for i,value in enumerate(sorted(l3DomDNList)):
            print "[%s]: %s" % (i+1, value)
    print "\n"

    l3DomChoice = None
    while l3DomChoice is None:
        l3DomChoice = raw_input("Which Type of L3 Domain Would You Like to Use for L3 Out Replacement?    :")
        try:
            l3DomChoice = int(l3DomChoice)
            if l3DomChoice < 1 or l3DomChoice >len(l3DomDNList): raise ValueError("")
        except ValueError as e:
                print "Please select a value between 1 and %s" % len(l3DomDNList)
                l3DomChoice = None

    for i, value in enumerate(sorted(l3DomDNList)):
                if l3DomChoice-1 == i:
                    l3Dom = value
    print "\n"
    print 'You have chosen "%s"\n' % l3Dom

    #################################
    # GET infraAccBaseGrp from APIC #
    #################################
    polGrpUrl = "/api/node/class/infraAccBaseGrp.json"
    polGrpResp = session.get(polGrpUrl)
    PolGrpJS = polGrpResp.json()

    if (l3If and l3PC and l3VPC):
        type = "All"
    elif (l3If and l3PC):
        type = "If-PC"
    elif (l3If and l3VPC):
        type = "If-VPC"
    elif (l3If):
        type = "If"
    elif (l3PC and l3VPC):
        type = "PC-SVI"
    elif l3PC:
        type = "PC"
    elif l3VPC:
        type = "VPC"
    else:
        type = None

    print "\n"

    if type == "All":
        print "Since Routed Ints/SubInts, PCs, and SVIs are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        l3PC = getL3PC(session)
        l3VPC = getL3VPC(session)

    elif type == "If-PC":
        print "Since Routed Ints/SubInts, and PCs are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        l3PC = getL3PC(session)
        l3VPC = False

    elif type == "If-VPC":
        print "Since Routed Ints/SubInts, and VPCs are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        l3PC = False
        l3VPC = getL3VPC(session)

    elif type == "If":
        print "Since Routed Ints/SubInts are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        l3PC = False
        l3VPC = False

    elif type == "PC-SVI":
        print "Since PCs and VPCs are used, we will need to select all options for replacement"
        l3If = False
        l3PC = getL3PC(session)
        l3VPC = getL3VPC(session)

    elif type == "PC":
        print "Since PCs are used, we will need to select which PC for replacement"
        l3If = False
        l3PC = getL3PC(session)
        l3VPC = False

    elif type == "VPC":
        print "Since VPCs are used, we will need to select which VPC to use for replacement"
        l3If = False
        l3PC = False
        l3VPC = getL3VPC(session)

    return l3Dom, l3If, l3PC, l3VPC


def getL3PC(session):

    polGrpDNList = []
    bundleDNList = []

    #################################
    # GET infraAccBaseGrp from APIC #
    #################################
    polGrpUrl = "/api/node/class/infraAccBaseGrp.json"
    polGrpResp = session.get(polGrpUrl)
    PolGrpJS = polGrpResp.json()

    polGrpCount = PolGrpJS['totalCount']
    for i in range(0, int(polGrpCount)):
        if "infraAccBndlGrp" in PolGrpJS["imdata"][i]:
            polGrpDN = PolGrpJS["imdata"][i]["infraAccBndlGrp"]["attributes"]["dn"]
            polGrpDNList.append(polGrpDN)

    for i, value in enumerate(sorted(polGrpDNList)):
        print "[%s]: %s" % (i+1, value)
    print "\n"

    polGrpChoice = None
    while polGrpChoice is None:
        polGrpChoice = raw_input("Which Policy Group Would You Like to Use for L3 PC Replacement?         :")
        try:
            polGrpChoice = int(polGrpChoice)
            if polGrpChoice < 1 or polGrpChoice >len(polGrpDNList): raise ValueError("")
        except ValueError as e:
                print "Please select a value between 1 and %s" % len(polGrpDNList)
                polGrpChoice = None

    for i, value in enumerate(sorted(polGrpDNList)):
        if polGrpChoice-1 == i:
            polGroup = value

    print 'You have chosen "%s"' % polGroup
    print "\n"

    r1 =re.search("^uni\/infra\/funcprof\/accbundle-(?P<polGrp>.*)", polGroup)

    ##############################
    # GET fabricPathEp from APIC #
    ##############################
    pathEpUrl = "/api/node/class/fabricPathEp.json"
    pathEpResp = session.get(pathEpUrl)
    pathEpJS = pathEpResp.json()


    pathEpCount = pathEpJS['totalCount']
    for i in range(0, int(pathEpCount)):
        if r1.group("polGrp") in pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]:
            bundleDN = pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]
            bundleDNList.append(bundleDN)

    for i,value in enumerate(sorted(bundleDNList)):
        print "[%s]: %s" % (i+1, value)
    print "\n"

    bundleChoice = None
    while bundleChoice is None:
        bundleChoice = raw_input("Which Path Would You Like to Use for L3 PC Replacement?                 :")
        try:
            bundleChoice = int(bundleChoice)
            if bundleChoice < 1 or bundleChoice >len(bundleDNList): raise ValueError("")
        except ValueError as e:
            print "Please select a value between 1 and %s" % len(bundleDNList)
            portChoice = None

    for i, value in enumerate(sorted(bundleDNList)):
        if bundleChoice-1 == i:
            l3PCBundle = value

    print 'You have chosen "%s"' % l3PCBundle
    print "\n"

    return l3PCBundle

def getL3VPC(session):
    polGrpDNList = []
    bundleDNList = []

    #################################
    # GET infraAccBaseGrp from APIC #
    #################################
    polGrpUrl = "/api/node/class/infraAccBaseGrp.json"
    polGrpResp = session.get(polGrpUrl)
    PolGrpJS = polGrpResp.json()

    polGrpCount = PolGrpJS['totalCount']
    for i in range(0, int(polGrpCount)):
        if "infraAccBndlGrp" in PolGrpJS["imdata"][i]:
            polGrpDN = PolGrpJS["imdata"][i]["infraAccBndlGrp"]["attributes"]["dn"]
            polGrpDNList.append(polGrpDN)

    for i, value in enumerate(sorted(polGrpDNList)):
        print "[%s]: %s" % (i+1, value)
    print "\n"

    polGrpChoice = None
    while polGrpChoice is None:
        polGrpChoice = raw_input("Which Policy Group Would You Like to Use for L3 VPC Replacement?        :")
        try:
            polGrpChoice = int(polGrpChoice)
            if polGrpChoice < 1 or polGrpChoice >len(polGrpDNList): raise ValueError("")
        except ValueError as e:
                print "Please select a value between 1 and %s" % len(polGrpDNList)
                polGrpChoice = None

    for i, value in enumerate(sorted(polGrpDNList)):
        if polGrpChoice-1 == i:
            polGroup = value

    print 'You have chosen "%s"' % polGroup
    print "\n"

    r1 =re.search("^uni\/infra\/funcprof\/accbundle-(?P<polGrp>.*)", polGroup)

    ##############################
    # GET fabricPathEp from APIC #
    ##############################
    pathEpUrl = "/api/node/class/fabricPathEp.json"
    pathEpResp = session.get(pathEpUrl)
    pathEpJS = pathEpResp.json()


    pathEpCount = pathEpJS['totalCount']
    for i in range(0, int(pathEpCount)):
        if r1.group("polGrp") in pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]:
            bundleDN = pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]
            bundleDNList.append(bundleDN)

    for i,value in enumerate(sorted(bundleDNList)):
        print "[%s]: %s" % (i+1, value)
    print "\n"

    bundleChoice = None
    while bundleChoice is None:
        bundleChoice = raw_input("Which Path Would You Like to Use for L3 VPC Replacement?                :")
        try:
            bundleChoice = int(bundleChoice)
            if bundleChoice < 1 or bundleChoice >len(bundleDNList): raise ValueError("")
        except ValueError as e:
            print "Please select a value between 1 and %s" % len(bundleDNList)
            portChoice = None

    for i, value in enumerate(sorted(bundleDNList)):
        if bundleChoice-1 == i:
            l3VPCBundle = value

    print 'You have chosen "%s"' % l3VPCBundle
    print "\n"

    return l3VPCBundle

def getL3Int(session):

    portDNList   = []

    ##############################
    # GET fabricPathEp from APIC #
    ##############################
    pathEpUrl = "/api/node/class/fabricPathEp.json"
    pathEpResp = session.get(pathEpUrl)
    pathEpJS = pathEpResp.json()


    pathEpCount = pathEpJS['totalCount']
    for i in range(0, int(pathEpCount)):
        if "/pathep-[eth" in pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]:
            portDN = pathEpJS["imdata"][i]["fabricPathEp"]["attributes"]["dn"]
            portDNList.append(portDN)

    # Get POD
    podChoice = None
    while podChoice is None:
        podChoice = raw_input("Which Pod Will The Leaf Be Located? [%s-%s]                                :" % (MINIMUM_POD, MAXIMUM_POD))
        try:
            podChoice = int(podChoice)
            if podChoice > MAXIMUM_POD or podChoice < MINIMUM_POD: raise ValueError("")
        except ValueError as e:
            print "Pod ID must be between %s and %s" % (MINIMUM_POD, MAXIMUM_POD)
            podChoice = None

    #Get Leaf
    leafChoice = None
    while leafChoice is None:
        leafChoice = raw_input("Which Leaf will the port be Deployed?                                     :")
        try:
            leafChoice = int(leafChoice)
            if leafChoice > MAXIMUM_NODE or leafChoice < MINIMUM_NODE: raise ValueError("")
        except ValueError as e:
            print "Leaf ID must be between %s and %s" % (MINIMUM_NODE, MAXIMUM_NODE)
            leafChoice = None

    #Get Port
    portChoice = None
    while portChoice is None:
        portChoice = raw_input("Which Port Would You Like to Use for Replacement?                         :")
        try:
            portChoice = int(portChoice)
            if portChoice > MAXIMUM_PORT or portChoice < MINIMUM_PORT: raise ValueError("")
        except ValueError as e:
            print "Port ID must be between %s and %s" % (MINIMUM_PORT, MAXIMUM_PORT)
            portChoice = None

    l3Port = "topology/pod-" + str(podChoice) + "/paths-" + str(leafChoice) + "/pathep-[eth1/" + str(portChoice) + "]"
    if l3Port in portDNList:
        print 'You have chosen "%s"' % l3Port
    else:
        print "unable to find port in Fabric"
        sys.exit()

    return l3Port

def jsonParser(file):
    with open(file, "r") as js:
        parsed = json.load(js)

    totalEntries = parsed['totalCount']
    print "The Total number of Changes:                        %s" % len(parsed["imdata"])

    return sortAudits(parsed["imdata"])


def xmlParser(file):
    audits = []
    with open(file, "r") as f:
        root = etree.parse(f)
        for e in root.findall("./aaaModLR"):
            audits.append({"aaaModLR": {"attributes":dict(e.attrib)}})

    print "The Total number of Changes:                        %s" % len(audits)
    return sortAudits(audits)

def sortAudits(audits):
    """
    sort audits based on timestamp with oldest timestamp first.  For audits that have exact timestamp, the object with
    shortest dn string is first.
    """
    buckets = {}    # dict of audits with same ts indexed by key
    for a in audits:
        ts = parse_timestamp(a["aaaModLR"]["attributes"]["created"])
        if ts is None:
            print "failed to parse timestamp for audit(%s): %s" % (a["aaaModLR"]["attributes"]["created"], a)
            sys.exit(1)
        a["aaaModLR"]["attributes"]["_ts"] = ts
        if ts not in buckets: buckets[ts] = []
        buckets[ts].append(a)

    results = []
    for ts in sorted(buckets):
        b = buckets[ts]
        for a in sorted(b, key=lambda b: len(b["aaaModLR"]["attributes"]["dn"])):
            results.append(a)

    return results



def getTotals(dateSorted):

    l3If  = False
    l3PC  = False
    l3VPC = False
    vmm   = False
    phys  = False
    port = False
    mgmt  = False

    #Get Total Number of Config Changes Per Tenant Object

    #Total Global Tenant Objects
    all = []
    for entry in dateSorted:
        r1 = re.search("uni\/(?P<gltn>tn-)", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("gltn") in entry["aaaModLR"]["attributes"]["dn"]:
                    all.append(entry)
        else:
            mgmt = True
            continue


    #Total Tenant Objects
    allTN = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-(?P<tn>[^\]\/]+)\]", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("tn") in entry["aaaModLR"]["attributes"]["dn"]:
                    allTN.append(entry)

        else:
            continue

    #Total VRF Objects
    allVrf = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<vrf>ctx-)", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("vrf") in entry["aaaModLR"]["attributes"]["dn"]:
                    allVrf.append(entry)

        else:
            continue

    #Total L3Out Objects
    allL3Out = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<l3>out-)", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("l3") in entry["aaaModLR"]["attributes"]["dn"]:
                    allL3Out.append(entry)
                    r2 = re.search("(?P<l3if>rspathL3OutAtt-.*(?=pathep)pathep-\[eth1\/)", entry["aaaModLR"]["attributes"]["dn"])
                    if r2 is not None:
                        if r2.group("l3if") in entry ["aaaModLR"]["attributes"]["dn"]:
                            l3If = True
                    r3 = re.search("(?P<l3PC>rspathL3OutAtt-\[topology\/pod-[0-9]+\/paths-(?P<node>[0-9]+)\/pathep-\[[^eth1\/]+)",
                                   entry["aaaModLR"]["attributes"]["dn"])
                    if r3 is not None:
                        if r3.group("l3PC") in entry ["aaaModLR"]["attributes"]["dn"]:
                            l3PC = True
                    r4 = re.search("(?P<l3VPC>rspathL3OutAtt-.*(?=protpaths)protpaths-(?P<node1>[0-9]+))\-(?P<node2>[0-9]+)",
                                   entry["aaaModLR"]["attributes"]["dn"])
                    if r4 is not None:
                        if r4.group("l3VPC") in entry ["aaaModLR"]["attributes"]["dn"]:
                            l3VPC = True

        else:
            continue

    #Total App Profile Objects
    allApp = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/ap-(?P<app>[^\]/]+)\]", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("app") in entry["aaaModLR"]["attributes"]["dn"]:
                    allApp.append(entry)

        else:
            continue

    #Total EPG Objects
    allEPG = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<epg>epg-)", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("epg") in entry["aaaModLR"]["attributes"]["dn"]:
                    allEPG.append(entry)
                    r2 = re.search("(?P<vmm>rsdomAtt-\[uni\/vmmp-VMware)", entry["aaaModLR"]["attributes"]["dn"])
                    if r2 is not None:
                        if r2.group("vmm") in entry ["aaaModLR"]["attributes"]["dn"]:
                            vmm = True
                    r3 = re.search("(?P<phys>rsdomAtt-\[uni\/phys-)", entry["aaaModLR"]["attributes"]["dn"])
                    if r3 is not None:
                        if r3.group("phys") in entry["aaaModLR"]["attributes"]["dn"]:
                            phys = True
                    r4 = re.search("(?P<port>rspathAtt-\[topology)", entry["aaaModLR"]["attributes"]["dn"])
                    if r4 is not None:
                        if r4.group("port") in entry["aaaModLR"]["attributes"]["dn"]:
                            port = True
        else:
            continue

    #Total BD Objects
    allBD = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<bd>BD-)", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("bd") in entry["aaaModLR"]["attributes"]["dn"]:
                    allBD.append(entry)

        else:
            continue

    #Total Contract Objects
    allCon = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<con>brc-)", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("con") in entry["aaaModLR"]["attributes"]["dn"]:
                    allCon.append(entry)

        else:
            continue

    #Total Filter Objects
    allFlt = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<flt>flt-)", entry["aaaModLR"]["attributes"]["dn"])
        r2 = re.search("tn-mgmt", entry["aaaModLR"]["attributes"]["dn"])
        if r2 is None:
            if r1 is not None:
                if r1.group("flt") in entry["aaaModLR"]["attributes"]["dn"]:
                    allFlt.append(entry)
        else:
            continue

    print "The Total number of Global Tenant Config Changes:   %s" % len(all)
    print "The Total number of Tenant Config Changes:          %s" % len(allTN)
    print "The Total number of VRF Config Changes:             %s" % len(allVrf)
    print "The Total number of L3Out Config Changes:           %s" % len(allL3Out)
    print "The Total number of App-Profile Config Changes:     %s" % len(allApp)
    print "The Total number of EPG Config Changes:             %s" % len(allEPG)
    print "The Total number of BD Config Changes:              %s" % len(allBD)
    print "The Total number of Contract Config Changes:        %s" % len(allCon)
    print "The Total number of Filter Config Changes:          %s\n" % len(allFlt)

    return all, allTN, allVrf, allL3Out, allApp, allEPG, allBD, allCon, allFlt, l3If, l3PC, l3VPC, vmm, phys, port, mgmt

def env_setup(ip, usr, pwd, https, port):


    while ip is None:
        ip = raw_input("Enter IP of APIC      :")
        if len(ip) == 0:
            print "URL is required"
            ip = None

    while https is None:
        prot = raw_input("HTTPS? [y/n]          :")
        if prot == "n" or prot == "N":
            https = False
        elif prot == "y" or prot == "Y":
            https = True
        else :
            print "Please Enter Y or N"
            https = None

    default = False
    while port is None:
        port = raw_input("Enter Port [None]     :")
        if len(port) == 0:
            default = True
        if default == False:
            try:
                int(port)
            except ValueError:
                print "Please enter an integer for a Port Number"
                port = None

    if port and https:
        url = str("https://" + ip + ":" + port)
    elif port:
        url = str("http://" + ip + ":" + port)
    elif https:
        url = str("https://" + ip)
    else:
        url = str("http://" + ip)

# Load username from ARGS or Prompt
    if usr == "admin":
        print "Using Default Username: admin"
    while usr is None:
        usr = raw_input( "Enter username        : ")
        if len(usr)==0:
            print "Username is required"
            usr = None

# Load PW from ARGS or Prompt
    while pwd is None:
        pwd = getpass.getpass( "Enter admin password  : ")
        pwd2 = getpass.getpass("Re-enter password     : ")
        if len(pwd)==0:
            pwd = None
        elif pwd!=pwd2:
            print "Passwords do not match"
            pwd = None
        elif " " in pwd:
            print "No spaces allowed in password"
            pwd = None
    print "\n"

    session = Session(url, usr, pwd, verify_ssl=False)
    resp = session.login(timeout=60)
    if resp is None or not resp.ok:
            logger.error("failed to login with cert credentials")
            #return None
            sys.exit()

    return session

def reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, l3PC, l3VPC):

    if reMapObjects[0] in entry["aaaModLR"]["attributes"]["dn"] and isinstance(phyDom, str):
        entry["aaaModLR"]["attributes"]["dn"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % phyDom, entry["aaaModLR"]["attributes"]["dn"])
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % phyDom, entry["aaaModLR"]["attributes"]["changeSet"])
        entry["aaaModLR"]["attributes"]["affected"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % phyDom, entry["aaaModLR"]["attributes"]["affected"])
        entry["aaaModLR"]["attributes"]["descr"] = re.sub("uni.*(?=\s)", phyDom, entry["aaaModLR"]["attributes"]["descr"])
    if reMapObjects[1] in entry["aaaModLR"]["attributes"]["dn"] and isinstance(vmmDom, str):
        entry["aaaModLR"]["attributes"]["dn"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % vmmDom, entry["aaaModLR"]["attributes"]["dn"])
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % vmmDom, entry["aaaModLR"]["attributes"]["changeSet"])
        entry["aaaModLR"]["attributes"]["affected"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % vmmDom, entry["aaaModLR"]["attributes"]["affected"])
        entry["aaaModLR"]["attributes"]["descr"] = re.sub("uni.*(?=\s)", vmmDom, entry["aaaModLR"]["attributes"]["descr"])
    if reMapObjects[2] in entry["aaaModLR"]["attributes"]["dn"] and isinstance(l3Dom, str):
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % l3Dom, entry["aaaModLR"]["attributes"]["changeSet"])
    if reMapObjects[3] in entry["aaaModLR"]["attributes"]["dn"] and isinstance(port, str):
        entry["aaaModLR"]["attributes"]["dn"] = re.sub("rspathAtt-\[[^]]+\]", "rspathAtt-[%s" % port, entry["aaaModLR"]["attributes"]["dn"])
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % port, entry["aaaModLR"]["attributes"]["changeSet"])
        entry["aaaModLR"]["attributes"]["affected"] = re.sub("rspathAtt-\[[^]]+\]", "rspathAtt-[%s" % port, entry["aaaModLR"]["attributes"]["affected"])
        entry["aaaModLR"]["attributes"]["descr"] = re.sub("topology.*(?=\s)", port, entry["aaaModLR"]["attributes"]["descr"])
    if reMapObjects[4] in entry["aaaModLR"]["attributes"]["dn"]:
        if l3If:
            r2 = re.search("(?P<l3if>rspathL3OutAtt-.*(?=pathep)pathep-\[eth1\/)", entry["aaaModLR"]["attributes"]["dn"])
            if r2 is not None:
                if r2.group("l3if") in entry ["aaaModLR"]["attributes"]["dn"] and isinstance(l3If, str):
                    entry["aaaModLR"]["attributes"]["dn"] = re.sub("rspathL3OutAtt-\[[^]]+\]", "rspathL3OutAtt-[%s" % l3If, entry["aaaModLR"]["attributes"]["dn"])
                    entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % l3If, entry["aaaModLR"]["attributes"]["changeSet"])
                    entry["aaaModLR"]["attributes"]["affected"] = re.sub("rspathL3OutAtt-\[[^]]+\]", "rspathL3OutAtt-[%s" % l3If, entry["aaaModLR"]["attributes"]["affected"])
        if l3PC:
            r3 = re.search("(?P<l3PC>rspathL3OutAtt-\[topology\/pod-[0-9]+\/paths-(?P<node>[0-9]+)\/pathep-\[[^eth1\/]+)", entry["aaaModLR"]["attributes"]["dn"])
            if r3 is not None:
                if r3.group("l3PC") in entry ["aaaModLR"]["attributes"]["dn"] and isinstance(l3PC, str):
                    entry["aaaModLR"]["attributes"]["dn"] = re.sub("rspathL3OutAtt-\[[^]]+\]", "rspathL3OutAtt-[%s" % l3PC, entry["aaaModLR"]["attributes"]["dn"])
                    entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % l3PC, entry["aaaModLR"]["attributes"]["changeSet"])
                    entry["aaaModLR"]["attributes"]["affected"] = re.sub("rspathL3OutAtt-\[[^]]+\]", "rspathL3OutAtt-[%s" % l3PC, entry["aaaModLR"]["attributes"]["affected"])
        if l3VPC:
            r4 = re.search("topology\/pod-(?P<pod>[0-9])\/protpaths-(?P<node1>[0-9]+)\-(?P<node2>[0-9]+)", str(l3VPC))
            r5 = re.search("(?P<l3VPC>rspathL3OutAtt-.*(?=protpaths)protpaths-(?P<node1>[0-9]+))\-(?P<node2>[0-9]+)", entry["aaaModLR"]["attributes"]["dn"])
            global pod
            pod = r4.group("pod")
            global node1
            node1 = r4.group("node1")
            global node2
            node2 = r4.group("node2")
            if r5 is not None:
                if r5.group("l3VPC") in entry ["aaaModLR"]["attributes"]["dn"] and isinstance(l3VPC, str):
                    entry["aaaModLR"]["attributes"]["dn"] = re.sub("rspathL3OutAtt-\[[^]]+\]", "rspathL3OutAtt-[%s" % l3VPC, entry["aaaModLR"]["attributes"]["dn"])
                    entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % l3VPC, entry["aaaModLR"]["attributes"]["changeSet"])
                    entry["aaaModLR"]["attributes"]["affected"] = re.sub("rspathL3OutAtt-\[[^]]+\]", "rspathL3OutAtt-[%s" % l3VPC, entry["aaaModLR"]["attributes"]["affected"])

    if reMapObjects[5] in entry["aaaModLR"]["attributes"]["dn"]:
        if l3VPC:
            entry["aaaModLR"]["attributes"]["dn"] = re.sub("rsnodeL3OutAtt-\[topology\/pod-[0-9]\/node-[^]]+", "rsnodeL3OutAtt-[topology/pod-%s/node-%s" % (pod, node1), entry["aaaModLR"]["attributes"]["dn"])
            entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:topology\/pod-[0-9]\/node-[^ ,]+", "tDn:topology/pod-%s/node-%s" % (pod, node1), entry["aaaModLR"]["attributes"]["changeSet"])
            entry["aaaModLR"]["attributes"]["affected"] = re.sub("rsnodeL3OutAtt-\[topology\/pod-[0-9]\/node-[^]]+", "rsnodeL3OutAtt-[topology/pod-%s/node-%s" % (pod, node1), entry["aaaModLR"]["attributes"]["affected"])
            node1 = node2

    print "Object Needs to be Re-Mapped To:"
    prettyPrint =  json.dumps(entry, indent=2)
    print prettyPrint

    return entry

def replayAudits(session, selection, audits, waitTime, step, vmm, phys, port, l3If, l3PC, l3VPC, catalog):
    if waitTime is not None:
        wait = int(waitTime)
    else:
        wait = 3

    if catalog is None:
        # attempt to pull catalog from current apic session
        page = session.get("/doc/model/MESSAGE-CATALOG.txt")
        lines = page.content.split("\n")
    else:
        # read the provided catalog filename
        try:
            with open(catalog, "r") as f:
                lines = f.readlines()
        except IOError as e:
                print "unable to read catalog file (%s): %s" % (catalog, e)
                sys.exit(1)
    codes = {}
    current_code = None
    event_code_regex = re.compile("\[EVENT CODE\]:[ \t]*E?(?P<event_code>[0-9]+)")
    class_code_regex = re.compile("(?i)\[MO CLASS\]:[ \t]*(?P<namespace>[a-z0-9+]+):(?P<class>[a-z0-9]+)")
    for l in lines:
        if current_code is None:
            r = event_code_regex.search(l)
            if r is not None:
                current_code = r.group("event_code")
        else:
            r = class_code_regex.search(l)
            if r is not None:
                codes[current_code] = r.group("namespace") + r.group("class")
                current_code = None
    
    # verify we were able to get at few catalog codes
    if len(codes)<1:
        from_apic = "(pulled from APIC)" if catalog is None else "from provided catalog file %s" % catalog
        print "unable to find event codes in catalog %s" % from_apic
        sys.exit(1)


    if "1" in selection or "6" in selection:
        if vmm == True:
            vmmDom = getVMMUserInfo(session)
        if phys == True or port == True:
            phyDom, port = getPhyUserInfo(session)
    else:
        vmm = False
        phys = False
        port = False

    if "1" in selection or "4" in selection:
        l3Dom, l3If, l3PC, l3VPC = getL3UserInfo(session, l3If, l3PC, l3VPC)
    else:
        l3Dom = False
        l3If = False
        l3PC = False
        l3VPC = False

    if "2" in selection or "3" in selection or "5" in selection or "7" in selection or "8" in selection or "9" in selection:
        vmm = False
        phys = False
        port = False
        l3Dom = False
        l3If = False
        l3PC = False
        l3V
        PC = False
    for entry in audits:
        try:
            #if selection == "1":
            prettyPrint =  json.dumps(entry, indent=2)
            print prettyPrint
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                for object in range(0, len(reMapObjects)):
                        if reMapObjects[object] in r2.group("url"):
                            if (vmm and phys and l3If and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                            elif (vmm and phys and l3If and l3PC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, l3PC, False)
                            elif (vmm and phys and l3If and l3VPC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, False, l3VPC)
                            elif (vmm and phys and l3If):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, False, False)
                            elif (vmm and phys and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, False, l3PC, l3VPC)
                            elif (vmm and phys and l3PC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, False, l3PC, False)
                            elif (vmm and phys and l3VPC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, False, False, l3VPC)
                            elif (vmm and phys):
                                entry = reMap(entry, vmmDom, phyDom, port, False, False, False, False)
                            elif (vmm and l3If and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, l3PC, l3VPC)
                            elif (vmm and l3If and l3PC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, l3PC, False)
                            elif (vmm and l3If and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, False, l3VPC)
                            elif (vmm and l3If):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, False, False)
                            elif (vmm and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, False, l3PC, l3VPC)
                            elif (vmm and l3PC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, False, l3PC, False)
                            elif (vmm and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, False, False, l3VPC)
                            elif (phys and port and l3If and l3PC and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                            elif (phys and l3If and l3PC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, l3PC, False)
                            elif (phys and l3If and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, False, l3VPC)
                            elif (phys and l3If):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, False, False)
                            elif (phys and l3PC and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, False, l3PC, l3VPC)
                            elif (phys and l3PC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, False, l3PC, False)
                            elif (phys and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, False, False, l3VPC)
                            elif (l3If and l3PC and l3VPC):
                                entry = reMap(entry, False, False, False, l3Dom, l3If, l3PC, l3VPC)
                            elif (l3If and l3PC):
                                entry = reMap(entry, False, False, False, l3Dom, l3If, l3PC, False)
                            elif (l3If and l3VPC):
                                entry = reMap(entry, False, False, False, l3Dom, l3If, False, l3VPC)
                            elif l3If:
                                entry = reMap(entry, False, False, False, l3Dom, l3If, False, False)
                            elif (l3PC and l3VPC):
                                entry = reMap(entry, False, False, False, l3Dom, False, l3PC, l3VPC)
                            elif l3PC:
                                entry = reMap(entry, False, False, False, l3Dom, False, l3PC, False)
                            elif l3VPC:
                                entry = reMap(entry, False, False, False, l3Dom, False, False, l3VPC)
                            elif (vmm and phys):
                                entry = reMap(entry, vmmDom, phyDom, port, False, False, False, False)
                            elif vmm:
                                entry = reMap(entry, vmmDom, False, False, False, False, False, False)
                            elif phys:
                                entry = reMap(entry, False, phyDom, port, False, False, False, False)
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    #r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    code = re.sub("^E","", entry["aaaModLR"]["attributes"]["code"])
                    if code in codes:
                        className = codes[code]
                    else:
                        print "Could not find Audit Code (%s) in Code List.  Are you running the same version as Audits?"%(
                            code)
                        sys.exit()

                    url = "/api/mo/" + r2.group("url") + ".json"

                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    # Send POST to APIC with Audit Data
                    POST = session.push_to_apic(url, data)
                    if not POST.ok:
                        print "POST was not Successful with:"
                        print "%s to:" % data
                        print "%s" % url
                    else:
                        print "Got 200 OK From POST with:"
                        print "%s to:" % data
                        print "%s" % url


                    time.sleep(wait)

                    # If Stepping is enabled, prompt for user input before
                    # proceeding to the next entry
                    # don't prompt on last entry
                    if entry != audits[len(audits)-1]:
                        if step != None:
                            user_input = None
                            while user_input == None:
                                user_input = raw_input( "Press Enter to Continue        : ")
                                if len(user_input) != 0:
                                    print "Please press Enter to Continue"

            elif entry["aaaModLR"]["attributes"]["ind"] == "modification":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                for object in range(0, len(reMapObjects)):
                        if reMapObjects[object] in r2.group("url"):
                            if (vmm and phys and l3If and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                            elif (vmm and phys and l3If and l3PC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, l3PC, False)
                            elif (vmm and phys and l3If and l3SVI):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, False, l3VPC)
                            elif (vmm and phys and l3If):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, False, False)
                            elif (vmm and phys and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, False, l3PC, l3VPC)
                            elif (vmm and phys and l3PC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, False, l3PC, False)
                            elif (vmm and phys and l3VPC):
                                entry = reMap(entry, vmmDom, phyDom, port, l3Dom, False, False, l3VPC)
                            elif (vmm and phys):
                                entry = reMap(entry, vmmDom, phyDom, port, False, False, False, False)
                            elif (vmm and l3If and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, l3PC, l3VPC)
                            elif (vmm and l3If and l3PC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, l3PC, False)
                            elif (vmm and l3If and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, False, l3VPC)
                            elif (vmm and l3If):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, l3If, False, False)
                            elif (vmm and l3PC and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, False, l3PC, l3VPC)
                            elif (vmm and l3PC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, False, l3PC, False)
                            elif (vmm and l3VPC):
                                entry = reMap(entry, vmmDom, False, False, l3Dom, False, False, l3VPC)
                            elif (phys and port and l3If and l3PC and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                            elif (phys and l3If and l3PC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, l3PC, False)
                            elif (phys and l3If and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, False, l3VPC)
                            elif (phys and l3If):
                                entry = reMap(entry, False, phyDom, port, l3Dom, l3If, False, False)
                            elif (phys and l3PC and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, False, l3PC, l3VPC)
                            elif (phys and l3PC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, False, l3PC, False)
                            elif (phys and l3VPC):
                                entry = reMap(entry, False, phyDom, port, l3Dom, False, False, l3VPC)
                            elif (l3If and l3PC and l3VPC):
                                entry = reMap(entry, False, False, False, l3Dom, l3If, l3PC, l3VPC)
                            elif (l3If and l3PC):
                                entry = reMap(entry, False, False, False, l3Dom, l3If, l3PC, False)
                            elif (l3If and l3VPC):
                                entry = reMap(entry, False, False, False, l3Dom, l3If, False, l3VPC)
                            elif l3If:
                                entry = reMap(entry, False, False, False, l3Dom, l3If, False, False)
                            elif (l3PC and l3VPC):
                                entry = reMap(entry, False, False, False, l3Dom, False, l3PC, l3VPC)
                            elif l3PC:
                                entry = reMap(entry, False, False, False, l3Dom, False, l3PC, False)
                            elif l3VPC:
                                entry = reMap(entry, False, False, False, l3Dom, False, False, l3VPC)
                            elif (vmm and phys):
                                entry = reMap(entry, vmmDom, phyDom, port, False, False, False, False)
                            elif vmm:
                                entry = reMap(entry, vmmDom, False, False, False, False, False, False)
                            elif phys:
                                entry = reMap(entry, False, phyDom, port, False, False, False, False)
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[a-zA-Z0-9]+) \(Old:[ ]*(?P<old>.+?) New:[ ]*(?P<new>[^)]*)\)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key").strip()] = m.group("new").strip()
                    code = re.sub("^E","", entry["aaaModLR"]["attributes"]["code"])
                    if code in codes:
                        className = codes[code]
                    else:
                        print "Could not find Audit Code (%s) in Code List.  Are you running the same version as Audits?"%(
                            code)
                        sys.exit()
                    #r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    #if r4.group("class") in classes:
                    #    className =  classes[r4.group("class")]
                    url = "/api/mo/" + r2.group("url") + ".json"
                    data = {className:{"attributes":attributes}}

                    POST = session.push_to_apic(url, data)
                    if not POST.ok:
                        badPost = []
                        print "POST was not Successful with:"
                        print "%s to:" % data
                        print "%s" % url
                        badPost.append(entry)
                    else:
                        goodPost = []
                        print "Got 200 OK From POST with:"
                        print "%s to:" % data
                        print "%s" % url
                        goodPost.append(entry)
                    time.sleep(wait)

                    # If Stepping is enabled, prompt for user input before
                    # proceeding to the next entry
                    # don't prompt on last entry
                    if entry != audits[len(audits)-1]:
                        if step != None:
                            user_input = None
                            while user_input == None:
                                user_input = raw_input( "Press Enter to Continue        : ")
                                if len(user_input) != 0:
                                    print "Please press Enter to Continue"
        except:
            import traceback
            print traceback.format_exc()
            continue


def main(file, ip, username, password, https, port, waitTime, step, xml, json, catalog, start_time, end_time):

    # Get Connection Info From User and Build a Session Object to APIC
    session = env_setup(ip, username, password, https, port)

    if xml:
        dateSorted = xmlParser(file)
    elif json:
        # Sort the JSON
        dateSorted = jsonParser(file)

    # remove anything outside of start/end timestamps
    min_time = 0 if start_time is None else start_time
    max_time = 0xfffffffffffffff if end_time is None else end_time
    filtered = []
    for a in dateSorted:
        if a["aaaModLR"]["attributes"]["_ts"] >= min_time and a["aaaModLR"]["attributes"]["_ts"] <= max_time:
            filtered.append(a)
        else:
            logger.debug("skipping audit %.02f outside of range (%s, %s)" % (a["aaaModLR"]["attributes"]["_ts"],
                min_time, max_time))
    dateSorted = filtered
    if start_time is not None or end_time is not None:
        print "Number of filtered Changes :                        %s" % len(dateSorted)

    #prettyPrint =  json.dumps(dateSorted, indent=2)
    #print prettyPrint

    # Get Totals and Determine if VMM/Phys Domains are in use.  Also determine what interfaces are used for L3 Out
    all, allTN, allVrf, allL3Out, allApp, allEPG, allBD, allCon, allFlt, l3If, l3PC, l3VPC, vmm, phys, port, mgmt = getTotals(dateSorted)

    if mgmt is True:
        print "Found Changes to MGMT Tenant. Skipping...!"
    if vmm is True:
        print "Found VMM Domains in EPG Audits!"
    if phys is True:
        print "Found Physical Domains in EPG Audits!"
    if port is True:
        print "Found EPG Static Paths in EPG Audits!"
    if l3If is True:
        print "Found Routed Interfaces / Sub-Interfaces in L3 Out Audits!"
    if l3PC is True:
        print "Found PC Interfaces in L3 Out Audits!"
    if l3VPC is True:
        print "Found VPC Interfaces in L3 Out Audits!"

    print "\n"

    selections = {
        "1": all,
        "2": allTN,
        "3": allVrf,
        "4": allL3Out,
        "5": allApp,
        "6": allEPG,
        "7": allBD,
        "8": allCon,
        "9": allFlt
    }

    print "[1]: All Global Tenant Config"
    print "[2]: All Tenant Config"
    print "[3]: All VRF Config"
    print "[4]: All L3Out Config"
    print "[5]: All App Profile Config"
    print "[6]: All EPG Config"
    print "[7]: All BD Config"
    print "[8]: All Con Config"
    print "[9]: All Flt Config"

    selection = None
    while selection is None:
        selection = raw_input( "Which Audits would you like to Replay?                                    : ")
        if len(selection) ==  0 or selection not in selections:
            print "Please select a valid option"
            selection = None
    print "\n"


    replayAudits(session, selection, selections[selection], waitTime, step, vmm, phys, port, l3If, l3PC, l3VPC, catalog)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--file", action="store", help="filename", dest="file")
    parser.add_argument("--xml", action="store_true", help="input in xml format", dest="xml")
    parser.add_argument("--json", action="store_true", help="input in json format", dest="json")
    parser.add_argument("--ip", action="store", dest="ip",help="APIC URL", default=None)
    parser.add_argument("--username", action="store", dest="username",help="admin username", default="admin")
    parser.add_argument("--password", action="store", dest="password",help="admin password", default=None)
    parser.add_argument("--https", action="store_true", dest="https",help="Specifies whether to use HTTPS authentication", default=None)
    parser.add_argument("--port", action="store", dest="port",help="port number to use for APIC communicaton", default=None)
    parser.add_argument("--catalog", action="store", dest="catalog", default=None,
        help="manually specify MESSAGE-CATALOG.txt from version of code audits were pulled from")
    parser.add_argument("--startTime", action="store", dest="startTime",
        help="Time to begin deploying Audits.  Must be in the following Format: YYYY-MM-DDTHH:MM:SS", default=None)
    parser.add_argument("--endTime", action="store", dest="endTime",
        help="Time to Stop deploying Audits.  Must be in the following Format: YYYY-MM-DDTHH:MM:SS", default=None)
    parser.add_argument("--waitTime", action="store", dest="time",help="Time in seconds to wait between changes", default=None)
    parser.add_argument("--step", action="store_true", dest="step",help="Prompt For User input between each step", default=None)
    parser.add_argument("--debug", action="store", help="debug level", dest="debug", default="ERROR")
    args = parser.parse_args()

    start_time = args.startTime
    end_time = args.endTime
    if start_time is not None:
        start_time = parse_timestamp(start_time)
        if start_time is None: 
            print "invalid start time %s (use --help for help)" % args.startTime
            sys.exit(1)
    if end_time is not None:
        end_time = parse_timestamp(end_time)
        if end_time is None: 
            print "invalid end time %s (use --help for help)" % args.endTime
            sys.exit(1)

    

    # configure logging
    logger = logging.getLogger("")
    logger.setLevel(logging.WARN)
    logger_handler = logging.StreamHandler(sys.stdout)
    fmt ="%(asctime)s.%(msecs).03d %(levelname)8s %(filename)"
    fmt+="16s:(%(lineno)d): %(message)s"
    logger_handler.setFormatter(logging.Formatter(
        fmt=fmt,
        datefmt="%Z %Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(logger_handler)
    # set debug level
    args.debug = args.debug.upper()
    if args.debug == "DEBUG": logger.setLevel(logging.DEBUG)
    if args.debug == "INFO": logger.setLevel(logging.INFO)
    if args.debug == "WARN": logger.setLevel(logging.WARN)
    if args.debug == "ERROR": logger.setLevel(logging.ERROR)

    main(args.file, args.ip, args.username, args.password, args.https, args.port, args.time, args.step, args.xml, 
        args.json, args.catalog, start_time, end_time)

