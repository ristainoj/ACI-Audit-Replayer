__author__ = 'josephristaino'

import os, sys, logging, getpass, re, json, time, requests
from acisession import Session
from lxml import html


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
        "Member",
        "rsnodeL3OutAtt"
    ]

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

    print "\n"

    if type == "All":
        print "Since Routed Ints/SubInts, PCs, and SVIs are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        l3PC = getL3PC(session)
        l3VPC = getL3VPC(session)
        return l3Dom, l3If, l3PC, l3VPC

    elif type == "If-PC":
        print "Since Routed Ints/SubInts, and PCs are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        l3PC = getL3PC(session)
        return l3Dom, l3If, l3PC, ""

    elif type == "If-VPC":
        print "Since Routed Ints/SubInts, and VPCs are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        l3VPC = getL3VPC(session)
        return l3Dom, l3If, "", l3VPC

    elif type == "If":
        print "Since Routed Ints/SubInts are used, we will need to select all options for replacement"
        l3If = getL3Int(session)
        return l3Dom, l3If, "", ""

    elif type == "PC-SVI":
        print "Since PCs and VPCs are used, we will need to select all options for replacement"
        l3PC = getL3PC(session)
        l3VPC = getL3VPC(session)
        return l3Dom, "", l3PC, l3VPC

    elif type == "PC":
        print "Since PCs are used, we will need to select which PC for replacement"
        l3PC = getL3PC(session)
        return l3Dom, "", l3PC, ""

    elif type == "VPC":
        print "Since VPCs are used, we will need to select which VPC to use for replacement"
        l3VPC = getL3VPC(session)
        return l3Dom, "", "", l3VPC


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
            if bundleChoice < 1 or bundleChoice >len(bundleChoice): raise ValueError("")
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
    print "The Total number of Changes:                        %s" % totalEntries

    #Sort Audit Entries by Created Date/Time: Oldest --> Newest
    dateSorted = []
    for i in range(int(totalEntries)-1, -1, -1):
        dateSorted.append(parsed["imdata"][i])

    return dateSorted

def getTotals(dateSorted):

    l3If  = False
    l3PC  = False
    l3VPC = False
    vmm   = False
    phys  = False

    #Get Total Number of Config Changes Per Tenant Object

    #Total Global Tenant Objects
    all = []
    for entry in dateSorted:
        r1 = re.search("uni\/(?P<gltn>tn-)", entry["aaaModLR"]["attributes"]["dn"])
        if r1 is not None:
            if r1.group("gltn") in entry["aaaModLR"]["attributes"]["dn"]:
                all.append(entry)


    #Total Tenant Objects
    allTN = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-(?P<tn>[^\]\/]+)\]", entry["aaaModLR"]["attributes"]["dn"])
        if r1 is not None:
            if r1.group("tn") in entry["aaaModLR"]["attributes"]["dn"]:
                allTN.append(entry)


    #Total VRF Objects
    allVrf = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<vrf>ctx-)", entry["aaaModLR"]["attributes"]["dn"])
        if r1 is not None:
            if r1.group("vrf") in entry["aaaModLR"]["attributes"]["dn"]:
                allVrf.append(entry)

    #Total L3Out Objects
    allL3Out = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<l3>out-)", entry["aaaModLR"]["attributes"]["dn"])
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

    #Total App Profile Objects
    allApp = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/ap-(?P<app>[^\]/]+)\]", entry["aaaModLR"]["attributes"]["dn"])
        if r1 is not None:
            if r1.group("app") in entry["aaaModLR"]["attributes"]["dn"]:
                allApp.append(entry)

    #Total EPG Objects
    allEPG = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<epg>epg-)", entry["aaaModLR"]["attributes"]["dn"])
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

    #Total BD Objects
    allBD = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<bd>BD-)", entry["aaaModLR"]["attributes"]["dn"])
        if r1 is not None:
            if r1.group("bd") in entry["aaaModLR"]["attributes"]["dn"]:
                allBD.append(entry)

    #Total Contract Objects
    allCon = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<con>brc-)", entry["aaaModLR"]["attributes"]["dn"])
        if r1 is not None:
            if r1.group("con") in entry["aaaModLR"]["attributes"]["dn"]:
                allCon.append(entry)

    #Total Filter Objects
    allFlt = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<flt>flt-)", entry["aaaModLR"]["attributes"]["dn"])
        if r1 is not None:
            if r1.group("flt") in entry["aaaModLR"]["attributes"]["dn"]:
                allFlt.append(entry)

    print "The Total number of Global Tenant Config Changes:   %s" % len(all)
    print "The Total number of Tenant Config Changes:          %s" % len(allTN)
    print "The Total number of VRF Config Changes:             %s" % len(allVrf)
    print "The Total number of L3Out Config Changes:           %s" % len(allL3Out)
    print "The Total number of App-Profile Config Changes:     %s" % len(allApp)
    print "The Total number of EPG Config Changes:             %s" % len(allEPG)
    print "The Total number of BD Config Changes:              %s" % len(allBD)
    print "The Total number of Contract Config Changes:        %s" % len(allCon)
    print "The Total number of Filter Config Changes:          %s\n" % len(allFlt)

    return all, allTN, allVrf, allL3Out, allApp, allEPG, allBD, allCon, allFlt, l3If, l3PC, l3VPC, vmm, phys

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

def reMap(entry, vmmDom=False, phyDom=False, port=False, l3Dom=False, l3If=False, l3PC=False, l3SVI=False):

    if reMapObjects[0] in entry["aaaModLR"]["attributes"]["dn"]:
        entry["aaaModLR"]["attributes"]["dn"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % phyDom, entry["aaaModLR"]["attributes"]["dn"])
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % phyDom, entry["aaaModLR"]["attributes"]["changeSet"])
        entry["aaaModLR"]["attributes"]["affected"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % phyDom, entry["aaaModLR"]["attributes"]["affected"])
        entry["aaaModLR"]["attributes"]["descr"] = re.sub("uni.*(?=\s)", phyDom, entry["aaaModLR"]["attributes"]["descr"])
    if reMapObjects[1] in entry["aaaModLR"]["attributes"]["dn"]:
        entry["aaaModLR"]["attributes"]["dn"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % vmmDom, entry["aaaModLR"]["attributes"]["dn"])
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % vmmDom, entry["aaaModLR"]["attributes"]["changeSet"])
        entry["aaaModLR"]["attributes"]["affected"] = re.sub("rsdomAtt-\[[^]]+\]", "rsdomAtt-[%s]" % vmmDom, entry["aaaModLR"]["attributes"]["affected"])
        entry["aaaModLR"]["attributes"]["descr"] = re.sub("uni.*(?=\s)", vmmDom, entry["aaaModLR"]["attributes"]["descr"])
    if reMapObjects[2] in entry["aaaModLR"]["attributes"]["dn"]:
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % l3Dom, entry["aaaModLR"]["attributes"]["changeSet"])
    if reMapObjects[3] in entry["aaaModLR"]["attributes"]["dn"]:
        entry["aaaModLR"]["attributes"]["dn"] = re.sub("rspathAtt-\[[^]]+\]", "rspathAtt-[%s" % port, entry["aaaModLR"]["attributes"]["dn"])
        entry["aaaModLR"]["attributes"]["changeSet"] = re.sub("tDn:[^ ,]+", "tDn:%s" % port, entry["aaaModLR"]["attributes"]["changeSet"])
        entry["aaaModLR"]["attributes"]["affected"] = re.sub("rspathAtt-\[[^]]+\]", "rspathAtt-[%s" % port, entry["aaaModLR"]["attributes"]["affected"])
        entry["aaaModLR"]["attributes"]["descr"] = re.sub("topology.*(?=\s)", port, entry["aaaModLR"]["attributes"]["descr"])

    print "Object Needs to be Re-Mapped To:"
    prettyPrint =  json.dumps(entry, indent=2)
    print prettyPrint

    return entry

def replayAudits(session, selection, audits, waitTime, step, vmm, phys, l3If, l3PC, l3VPC):
    if waitTime is not None:
        wait = int(waitTime)
    else:
        wait = 3

    # Need to build a dictionary of all Classes to use for each POST
    # Will do this by querying the API Docs and Regexing Classes
    page = session.get('/doc/html/LeftSummary.html')
    tree = html.fromstring(page.content)

    # Get List of All Classes from the Documentation
    classEntries = tree.xpath('//a[starts-with(@href, "MO")]/text()')

    # Append Namespace to Class Name and Dictionary Them
    classes = {}
    for entry in classEntries:
        namespace = re.search("(?P<key>vz|fv|vmm|l3ext|l2ext):(?P<value>\w+)", entry)
        if namespace is not None:
            classes[namespace.group("value")] = namespace.group("key") + namespace.group("value")


    if "1" in selection or "6" in selection:
        if vmm == True:
            vmmDom = getVMMUserInfo(session)
        if phys == True:
            phyDom, port = getPhyUserInfo(session)
    else:
        vmm = False
        phys = False

    if "1" in selection or "4" in selection:
        l3Dom, l3If, l3PC, l3VPC = getL3UserInfo(session, l3If, l3PC, l3VPC)
    else:
        l3If = False
        l3PC = False
        l3VPC = False

    for entry in audits:
        #if selection == "1":
        prettyPrint =  json.dumps(entry, indent=2)
        print prettyPrint
        if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
            r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
            for object in range(0, len(reMapObjects)):
                    if reMapObjects[object] in r2.group("url"):
                        if (vmm and phys and l3If and l3PC and l3VPC):
                            entry = reMap(entry, vmmDom, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                        elif (vmm and l3If and l3PC and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3If, l3PC, l3VPC)
                        elif (vmm and l3If and l3PC):
                            entry = reMap(entry, vmmDom, l3Dom, l3If, l3PC)
                        elif (vmm and l3If and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3If, l3VPC)
                        elif (vmm and l3If):
                            entry = reMap(entry, vmmDom, l3Dom, l3If)
                        elif (vmm and l3PC and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3PC, l3VPC)
                        elif (vmm and l3PC):
                            entry = reMap(entry, vmmDom, l3Dom, l3PC)
                        elif (vmm and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3VPC)
                        elif (phys and port and l3If and l3PC and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                        elif (phys and l3If and l3PC and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                        elif (phys and l3If and l3PC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3PC)
                        elif (phys and l3If and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3VPC)
                        elif (phys and l3If):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If)
                        elif (phys and l3PC and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3PC, l3VPC)
                        elif (phys and l3PC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3PC)
                        elif (phys and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3VPC)
                        elif (l3If and l3PC and l3VPC):
                            entry = reMap(entry, l3Dom, l3If, l3PC, l3VPC)
                        elif (l3If and l3PC):
                            entry = reMap(entry, l3Dom, l3If, l3PC)
                        elif (l3If and l3VPC):
                            entry = reMap(entry, l3Dom, l3If, l3VPC)
                        elif l3If:
                            entry = reMap(entry, l3Dom, l3If)
                        elif (l3PC and l3VPC):
                            entry = reMap(entry, l3Dom, l3PC, l3VPC)
                        elif l3PC:
                            entry = reMap(entry, l3Dom, l3PC)
                        elif l3VPC:
                            entry = reMap(entry, l3Dom, l3VPC)
                        elif (vmm and phys):
                            entry = reMap(entry, vmmDom, phyDom, port)
                        elif vmm:
                            entry = reMap(entry, vmmDom)
                        elif phys:
                            entry = reMap(entry, phyDom, port)
            r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
            if r2 is not None:
                attributes = {}
                r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                for m in r3:
                    attributes[m.group("key")] = m.group("value")
                r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                if r4.group("class") in classes:
                    className =  classes[r4.group("class")]

                # Since we are checking the "desc" for object name, "Subnet"
                # could be fvSubnet or l3extSubnet.  Need to be specific.
                if "BD" in entry["aaaModLR"]["attributes"]["dn"] and "subnet" in entry["aaaModLR"]["attributes"]["dn"]:
                    className = "fvSubnet"
                elif "instP" in entry["aaaModLR"]["attributes"]["dn"] and "extsubnet" in entry["aaaModLR"]["attributes"]["dn"]:
                    className = "l3extSubnet"

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
                        elif (vmm and l3If and l3PC and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3If, l3PC, l3VPC)
                        elif (vmm and l3If and l3PC):
                            entry = reMap(entry, vmmDom, l3Dom, l3If, l3PC)
                        elif (vmm and l3If and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3If, l3VPC)
                        elif (vmm and l3If):
                            entry = reMap(entry, vmmDom, l3Dom, l3If)
                        elif (vmm and l3PC and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3PC, l3VPC)
                        elif (vmm and l3PC):
                            entry = reMap(entry, vmmDom, l3Dom, l3PC)
                        elif (vmm and l3VPC):
                            entry = reMap(entry, vmmDom, l3Dom, l3VPC)
                        elif (phys and port and l3If and l3PC and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                        elif (phys and l3If and l3PC and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3PC, l3VPC)
                        elif (phys and l3If and l3PC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3PC)
                        elif (phys and l3If and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If, l3VPC)
                        elif (phys and l3If):
                            entry = reMap(entry, phyDom, port, l3Dom, l3If)
                        elif (phys and l3PC and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3PC, l3VPC)
                        elif (phys and l3PC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3PC)
                        elif (phys and l3VPC):
                            entry = reMap(entry, phyDom, port, l3Dom, l3VPC)
                        elif (l3If and l3PC and l3VPC):
                            entry = reMap(entry, l3Dom, l3If, l3PC, l3VPC)
                        elif (l3If and l3PC):
                            entry = reMap(entry, l3Dom, l3If, l3PC)
                        elif (l3If and l3VPC):
                            entry = reMap(entry, l3Dom, l3If, l3VPC)
                        elif l3If:
                            entry = reMap(entry, l3Dom, l3If)
                        elif (l3PC and l3VPC):
                            entry = reMap(entry, l3Dom, l3PC, l3VPC)
                        elif l3PC:
                            entry = reMap(entry, l3Dom, l3PC)
                        elif l3VPC:
                            entry = reMap(entry, l3Dom, l3VPC)
                        elif (vmm and phys):
                            entry = reMap(entry, vmmDom, phyDom, port)
                        elif vmm:
                            entry = reMap(entry, vmmDom)
                        elif phys:
                            entry = reMap(entry, phyDom, port)
            r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
            if r2 is not None:
                attributes = {}
                r3 = re.finditer("(?P<key>[a-zA-Z0-9]+) \(Old:[ ]*(?P<old>.+?) New:[ ]*(?P<new>[^)]*)\)", entry["aaaModLR"]["attributes"]["changeSet"])
                for m in r3:
                    attributes[m.group("key").strip()] = m.group("new").strip()
                r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                if r4.group("class") in classes:
                    className =  classes[r4.group("class")]
                url = "/api/mo/" + r2.group("url") + ".json"
                data = {className:{"attributes":attributes}}

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


def main(file, ip, username, password, https, port, waitTime, step):

    # Get Connection Info From User and Build a Session Object to APIC
    session = env_setup(ip, username, password, https, port)

    # Sort the JSON
    dateSorted = jsonParser(file)
    #prettyPrint =  json.dumps(dateSorted, indent=2)
    #print prettyPrint

    # Get Totals and Determine if VMM/Phys Domains are in use.  Alse determine what interfaces are used for L3 Out
    all, allTN, allVrf, allL3Out, allApp, allEPG, allBD, allCon, allFlt, l3If, l3PC, l3VPC, vmm, phys = getTotals(dateSorted)

    if vmm == True:
        print "Found VMM Domains in EPG Audits!"
    if phys == True:
        print "Found Physical Domains in EPG Audits!"
    if l3If == True:
        print "Found Routed Interfaces / Sub-Interfaces in L3 Out Audits!"
    if l3PC == True:
        print "Found PC Interfaces in L3 Out Audits!"
    if l3VPC == True:
        print "Found VPC Interfaces in L3 Out Audits!\n"

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


    replayAudits(session, selection, selections[selection], waitTime, step, vmm, phys, l3If, l3PC, l3VPC)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--file", action="store", help="filename", dest="file")
    #parser.add_argument("--xml", action="store_true", help="input in xml format", dest="xml")
    #parser.add_argument("--json", action="store_true", help="input in json format", dest="json")
    parser.add_argument("--ip", action="store", dest="ip",help="APIC URL", default=None)
    parser.add_argument("--username", action="store", dest="username",help="admin username", default="admin")
    parser.add_argument("--password", action="store", dest="password",help="admin password", default=None)
    parser.add_argument("--https", action="store_true", dest="https",help="Specifies whether to use HTTPS authentication", default=None)
    parser.add_argument("--port", action="store", dest="port",help="port number to use for APIC communicaton", default=None)
    parser.add_argument("--waitTime", action="store", dest="time",help="Time in seconds to wait between changes", default=None)
    parser.add_argument("--step", action="store_true", dest="step",help="Prompt For User input between each step", default=None)
    parser.add_argument("--debug", action="store", help="debug level", dest="debug", default="ERROR")
    args = parser.parse_args()

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

    main(args.file, args.ip, args.username, args.password, args.https, args.port, args.time, args.step)

