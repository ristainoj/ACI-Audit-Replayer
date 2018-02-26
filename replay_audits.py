__author__ = 'josephristaino'

import os, sys, logging, getpass, re, json, time, requests
from acisession import Session
from lxml import html


def getUserInfo(url, usr, pwd):

    #dnList = []
    polGrpDNList = {}
    stPathDNList = {}
    vmmDomDNList = {}
    phyDomDNList = {}

    intTypes = {
        1 : "Access Port",
        2 : "Port-Channel / VPC"
    }

    domTypes = {
        1 : "VMM Domain",
        2 : "Physical Domain"
    }

    session = Session(url, usr, pwd, verify_ssl=False)
    resp = session.login(timeout=60)
    if resp is None or not resp.ok:
            logger.error("failed to login with cert credentials")
            #return None
            sys.exit()

    for key, value in domTypes.iteritems():
        print "[" + str(key) + "]" + value

    dom = None
    vmmDom = False
    phyDom = False
    while dom is None:
        dom = raw_input("Which Type of Domain Would You Like to Use for Replacement?:")
        if len(dom) == 0 or dom not in str(domTypes):
            print "Please select a valid option"
            dom = None
        elif dom == "1":
            vmmDom = True
        elif dom == "2":
            phyDom = True

    if vmmDom == True:

        #########################
        # GET vmmDomP from APIC #
        #########################
        vmmDomUrl = "/api/node/class/vmmDomP.json"
        vmmDomResp = session.get(vmmDomUrl)
        vmmDomJS = vmmDomResp.json()

        vmmDomCount = vmmDomJS['totalCount']
        for i in range(0, int(vmmDomCount)):
            vmmDomDN = vmmDomJS["imdata"][i]["vmmDomP"]["attributes"]["dn"]
            vmmDomDNList[i+1] = vmmDomDN

        # Display vmmDomP info to User
        for key in sorted(vmmDomDNList):
            print "[%s]: %s" % (key, vmmDomDNList[key])

        vmmDomChoice = None
        while vmmDomChoice is None:
            vmmDomChoice = raw_input("Which Type of VMM Domain Would You Like to Use for Replacement?:")
            if len(vmmDomChoice) == 0  or vmmDomChoice not in str(vmmDomDNList):
                print "Please select a valid option"
                vmmDomChoice = None

        r1 = re.search("^uni\/.*?\/dom-(?P<vmmDom>.*)", vmmDomDNList[int(vmmDomChoice)])
        print "\n"
        print 'You have chosen "%s"' % r1.group("vmmDom")

    elif phyDom == True:

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
            phyDomDNList[i+1] = phyDomDN

        for key in sorted(phyDomDNList):
            print "[%s]: %s" % (key, phyDomDNList[key])

        phyDomChoice = None
        while phyDomChoice is None:
            phyDomChoice = raw_input("Which Type of Physical Domain Would You Like to Use for Replacement?:")
            if len(phyDomChoice) == 0 or phyDomChoice not in str(phyDomDNList):
                print "Please select a valid option"
                phyDomChoice = None

        r1 = re.search("^uni\/phys-(?P<phyDom>.*)", phyDomDNList[int(phyDomChoice)])
        print "\n"
        print 'You have chosen "%s"\n' % r1.group("phyDom")

        #################################
        # GET infraAccBaseGrp from APIC #
        #################################
        polGrpUrl = "/api/node/class/infraAccBaseGrp.json"
        polGrpResp = session.get(polGrpUrl)
        PolGrpJS = polGrpResp.json()

        # Display infraAccBaseGrp info to User
        for key, value in intTypes.iteritems():
            print "[" + str(key) + "]" + value

        polGrpType = None
        while polGrpType is None:
            polGrpType = raw_input("Which Type of Interface Would You Like to Use for Replacement?:")
            if len(polGrpType) == 0 or polGrpType not in str(intTypes):
                print "Please select a valid option"
                polGrpType = None
            elif polGrpType == "1":
                polGrpType = "infraAccPortGrp"
            elif polGrpType == "2":
                polGrpType = "infraAccBndlGrp"

        print "\n"

        polGrpCount = PolGrpJS['totalCount']
        for i in range(0, int(polGrpCount)):
            if polGrpType in PolGrpJS["imdata"][i]:
                polGrpDN = PolGrpJS["imdata"][i][polGrpType]["attributes"]["dn"]
                polGrpDNList[i+1] = polGrpDN

        for key in sorted(polGrpDNList):
            print "[%s]: %s" % (key, polGrpDNList[key])

        polGrpChoice = None
        while polGrpChoice is None:
            polGrpChoice = raw_input("Which Policy Group Would You Like to Use for Replacement?:")
            if len(polGrpChoice) == 0 or polGrpChoice not in str(polGrpDNList):
                print "Please select a valid option"
                polGrpChoice = None
        r1 =re.search("^uni\/infra\/funcprof\/accbundle-(?P<polGrp>.*)", polGrpDNList[int(polGrpChoice)])


        print "\n"
        print 'You have chosen "%s"' % r1.group("polGrp")

        #############################
        # GET fvRsPathAtt from APIC #
        #############################
        stPathUrl = "/api/node/class/fvRsPathAtt.json"
        stPathResp = session.get(stPathUrl)
        stPathJS = stPathResp.json()

        stPathCount = stPathJS['totalCount']
        for i in range(0, int(stPathCount)):
            if r1.group("polGrp") in stPathJS["imdata"][i]["fvRsPathAtt"]["attributes"]["dn"]:
                stPathDN = stPathJS["imdata"][i]["fvRsPathAtt"]["attributes"]["dn"]
                stPathDNList[i+1] = stPathDN

        for key in sorted(stPathDNList):
            print "[%s]: %s" % (key, stPathDNList[key])

        stPathChoice = None
        while stPathChoice is None:
            stPathChoice = raw_input("Which Static Path Would You Like to Use for Replacement?:")
            if len (stPathChoice) == 0 or stPathChoice not in str(polGrpDNList):
                print "Please select a valid option"
                stPathChoice = None
        r1 =re.search("^uni\/.*?\/.*?\/.*?\/rspathAtt-(?P<stPath>.*)", stPathDNList[int(stPathChoice)])

        print "\n"
        print 'You have chosen "%s"' % r1.group("stPath")

def jsonParser(file):
    with open(file, "r") as js:
        parsed = json.load(js)

    totalEntries = parsed['totalCount']
    print "The Total number of Changes:                        %s" % totalEntries

    #Sort Audit Entries by Created Date/Time: Oldest --> Newest
    #dateSorted = sorted(parsed["imdata"], key=lambda d: d["aaaModLR"]["attributes"]["created"])
    dateSorted = []
    for i in range(int(totalEntries) - 1, 0, -1):
        dateSorted.append(parsed["imdata"][i])

    #Pretty Print the JSON
    #prettyPrint =  json.dumps(dateSorted, indent=2)
    #print prettyPrint

    return dateSorted

def getTotals(dateSorted):

    #Get Total Number of Config Changes Per Tenant Object

    #Total Global Tenant Objects
    all = []
    for entry in dateSorted:
        print entry
        r1 = re.search("uni\/(?P<gltn>tn-)", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("gltn") in entry["aaaModLR"]["attributes"]["dn"]:
                all.append(entry)
        except:
            continue

    #Total Tenant Objects
    allTN = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-(?P<tn>[^\]\/]+)\]", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("tn") in entry["aaaModLR"]["attributes"]["dn"]:
                allTN.append(entry)
        except:
            continue

    #Total VRF Objects
    allVrf = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<vrf>ctx-)", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("vrf") in entry["aaaModLR"]["attributes"]["dn"]:
                allVrf.append(entry)
        except:
            continue

    #Total L3Out Objects
    allL3Out = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<l3>out-)", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("l3") in entry["aaaModLR"]["attributes"]["dn"]:
                allL3Out.append(entry)
        except:
            continue

    #Total App Profile Objects
    allApp = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/ap-(?P<app>[^\]/]+)\]", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("app") in entry["aaaModLR"]["attributes"]["dn"]:
                allApp.append(entry)
        except:
            continue

    #Total EPG Objects
    allEPG = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<epg>epg-)", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("epg") in entry["aaaModLR"]["attributes"]["dn"]:
                allEPG.append(entry)
        except:
            continue

    #Total BD Objects
    allBD = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<bd>BD-)", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("bd") in entry["aaaModLR"]["attributes"]["dn"]:
                allBD.append(entry)
        except:
            continue

    #Total Contract Objects
    allCon = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<con>brc-)", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("con") in entry["aaaModLR"]["attributes"]["dn"]:
                allCon.append(entry)
        except:
            continue

    #Total Filter Objects
    allFlt = []
    for entry in dateSorted:
        r1 = re.search("uni\/tn-.*\/(?P<flt>flt-)", entry["aaaModLR"]["attributes"]["dn"])
        try:
            if r1.group("flt") in entry["aaaModLR"]["attributes"]["dn"]:
                allFlt.append(entry)
        except:
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

    return all, allTN, allVrf, allL3Out, allApp, allEPG, allBD, allCon, allFlt

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

    return url, usr, pwd

def replayAudits(url, usr, pwd, selection, audits, waitTime):

    if waitTime is not None:
        wait = int(waitTime)
    else:
        wait = 3

    session = Session(url, usr, pwd, verify_ssl=False)
    resp = session.login(timeout=60)
    if resp is None or not resp.ok:
            logger.error("failed to login with cert credentials")
            #return None
            sys.exit()

    # Need to build a dictionary of all Classes to use for each POST
    # Will do this by querying the API Docs and Regexing Classes
    page = session.get('/doc/html/LeftSummary.html')
    tree = html.fromstring(page.content)

    # Get List of All Classes from the Documentation
    classEntries = tree.xpath('//a[starts-with(@href, "MO")]/text()')

    classes = {}
    for entry in classEntries:
        namespace = re.search("(?P<key>vz|fv|vmm|l3ext|l2ext):(?P<value>\w+)", entry)
        if namespace is not None:
            classes[namespace.group("value")] = namespace.group("key") + namespace.group("value")


    for entry in audits:
        if selection == "1":
            prettyPrint =  json.dumps(entry, indent=2)
            print prettyPrint
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]
                        print className
                    # Since we are checking the "desc" for object name, "Subnet"
                    # could be fvSubnet or l3extSubnet
                    if "BD" in entry["aaaModLR"]["attributes"]["dn"] and "subnet" in entry["aaaModLR"]["attributes"]["dn"]:
                        className = "fvSubnet"
                    elif "instP" in entry["aaaModLR"]["attributes"]["dn"] and "extsubnet" in entry["aaaModLR"]["attributes"]["dn"]:
                        className = "l3extSubnet"

                    url = "/api/mo/" + r2.group("url") + ".json"

                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    #print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)

        if selection == "2":
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                url = "/api/mo/" + r2.group("url") + ".json"
                if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                    data = {"fvTenant":{"attributes":{"status":"deleted"}}}
                elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                    data = {"fvTenant":{"attributes":{"name":r2.group("tn")}}}

                POST = session.push_to_apic(url, data)
                if POST is None or not resp.ok:
                    logger.error("failed to POST %s to %s") % data, url
                    return None

                time.sleep(wait)

        if selection == "3":
            #prettyPrint =  json.dumps(entry, indent=2)
            #print prettyPrint
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]

                    url = "/api/mo/" + r2.group("url") + ".json"
                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    #print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)

        if selection == "4":
            prettyPrint =  json.dumps(entry, indent=2)
            print prettyPrint
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]

                    url = "/api/mo/" + r2.group("url") + ".json"
                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)

        if selection == "5":
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]

                    url = "/api/mo/" + r2.group("url") + ".json"
                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    #print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)

        if selection == "6":
            prettyPrint =  json.dumps(entry, indent=2)
            print prettyPrint
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]

                    url = "/api/mo/" + r2.group("url") + ".json"
                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    #print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)

        if selection == "7":
            prettyPrint =  json.dumps(entry, indent=2)
            print prettyPrint
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]

                    url = "/api/mo/" + r2.group("url") + ".json"
                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    #print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)

        if selection == "8":
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]

                    url = "/api/mo/" + r2.group("url") + ".json"
                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    #print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)

        if selection == "9":
            if entry["aaaModLR"]["attributes"]["ind"] == "creation" or entry["aaaModLR"]["attributes"]["ind"] == "deletion":
                r2 = re.search("(?P<url>uni.*(?=]))", entry["aaaModLR"]["attributes"]["dn"])
                if r2 is not None:
                    attributes = {}
                    r3 = re.finditer("(?P<key>[^:, ]+):(?P<value>[^,]+)", entry["aaaModLR"]["attributes"]["changeSet"])
                    for m in r3:
                        attributes[m.group("key")] = m.group("value")
                    r4 = re.search("(?P<class>^\S*)", entry["aaaModLR"]["attributes"]["descr"])
                    if r4.group("class") in classes:
                        className =  classes[r4.group("class")]

                    url = "/api/mo/" + r2.group("url") + ".json"
                    if "deleted" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":{"status":"deleted"}}}
                    elif "created" in entry["aaaModLR"]["attributes"]["descr"]:
                        data = {className:{"attributes":attributes}}

                    #print url, data
                    POST = session.push_to_apic(url, data)
                    if POST is None or not resp.ok:
                        logger.error("failed to login with cert credentials")
                        return None
                    time.sleep(wait)




def main(file, ip, username, password, https, port, waitTime):

    # Get Connection Info From User for APIC
    url, usr, pwd = env_setup(ip, username, password, https, port)

    # Connect to APIC to Gather User Data and Configure Policies
    #getUserInfo(url, usr, pwd)

    dateSorted = jsonParser(file)
    #prettyPrint =  json.dumps(dateSorted, indent=2)
    #print prettyPrint

    all, allTN, allVrf, allL3Out, allApp, allEPG, allBD, allCon, allFlt = getTotals(dateSorted)

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
        selection = raw_input( "Which Audits would you like to Replay?        : ")
        if len(selection) ==  0 or selection not in selections:
            print "Please select a valid option"
            selection = None


    replayAudits(url, usr, pwd, selection, selections[selection], waitTime)


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

    main(args.file, args.ip, args.username, args.password, args.https, args.port, args.time)

