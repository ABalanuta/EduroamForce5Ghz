import os
import sys
import subprocess
from time import sleep


class myEduroam():

    def __init__(self):
        self.path = "/etc/NetworkManager/system-connections/eduroam"
        self.username = os.getlogin()
        self.select_interface()


    def get_interfaces(self):
        p = subprocess.Popen("iw dev", shell=True, stdout=subprocess.PIPE)
        lines = p.stdout.readlines()
        interfaces = list()
        for line in lines:
            if "Interface" in line:
                interfaces.append(line.split()[1])

        return interfaces

    def select_interface(self):
        interfaces = self.get_interfaces()

        if len(interfaces) > 1:
            for x in range(len(interfaces)):
                print str(x)+":", interfaces[x]
            select = int(raw_input('Select an Interface: '))
            print "Using Interface: ", interfaces[x]
            self.interface = interfaces[x]
        else:
            self.interface = interfaces[0]

    def scan_air(self):
        p = subprocess.Popen("sudo iwlist wlp2s0 scanning essid eduroam",\
                             shell=True, stdout=subprocess.PIPE)
        lines = p.stdout.readlines()

        stations = dict()
        for x in range(len(lines)):
            if "Address:" in lines[x]:
                mac = lines[x].split()[4]
                stations[mac] = {
                    'mac' : mac,
                    'channel' : int(lines[x+1].split(':')[1]),
                    'freq' : float(lines[x+2].split()[0].split(':')[1]),
                    'signal' : 120+int(lines[x+3].split()[2].split('=')[1])
                }
        self.stations = stations
        return stations

    def show_5ghz(self):
        ret = dict()
        for x, y in self.stations.items():
            if y['channel'] > 14:
                ret[x] = y
        self.fiveghzstations = ret
        return ret

    def pick_best(self):
        best_signal = -1
        cell = None
        for x, y in self.fiveghzstations.items():
            if y['signal'] > best_signal:
                best_signal = y['signal']
                cell = y
        self.cell = cell
        print cell
        return cell

    def set_cell(self):

        lines = self.read_eduroam_config()

        line_present = False
        for x in range(len(lines)):
            if "bssid=" in lines[x]:
                lines[x] = "bssid="+str(self.cell['mac'])+"\n"
                line_present = True
                break

        if not line_present:
            for x in range(len(lines)):
                if "mode=infrastructure" in lines[x]:
                    lines.insert(x+1, "bssid="+str(self.cell['mac'])+"\n")
                    break

        self.write_eduroam_config(lines)


    def unset_cell(self):
        lines = self.read_eduroam_config()
        for x in range(len(lines)):
            if "bssid=" in lines[x]:
                lines.pop(x)
                self.write_eduroam_config(lines)
                break

    def status_cell(self):
        lines = self.read_eduroam_config()
        for x in range(len(lines)):
            if "bssid=" in lines[x]:
                mac = lines[x].split('=')[1]
                return mac
        return None


    def read_eduroam_config(self):
        fd = open(self.path, 'r')
        lines = fd.readlines()
        fd.close()
        return lines

    def write_eduroam_config(self, lines):
        fd = open(self.path, 'w')
        fd.writelines(lines)
        fd.close()

    def kill_NM(self):
        p = subprocess.Popen("sudo killall NetworkManager", shell=True,\
                             stdout=subprocess.PIPE)
        lines = p.stdout.readlines()
        sleep(1)

    def start_NM(self):
        p = subprocess.Popen("sudo NetworkManager",shell=True,\
                             stdout=subprocess.PIPE)
        lines = p.stdout.readlines()
        sleep(1)

    def restart_NM(self):
        self.kill_NM()
        self.start_NM()

    def force_connect(self):
        p = subprocess.Popen('runuser -l '+self.username+' -c "'+\
                            "nmcli d connect "+str(self.interface)+'"',\
                             shell=True, stdout=subprocess.PIPE)
        lines = p.stdout.readlines()
        print lines

    def force_disconnect(self):
        p = subprocess.Popen('runuser -l '+self.username+' -c "'+\
                    "nmcli d disconnect "+str(self.interface)+'"',\
                     shell=True, stdout=subprocess.PIPE)
        lines = p.stdout.readlines()
        print lines




def print_usage():

    print "\nUsage:"
    print "\t sudo python2 "+str(sys.argv[0])+ " set    -Forces 5Ghz"
    print "\t sudo python2 "+str(sys.argv[0])+ " unset  -Returns to Auto"
    print "\t sudo python2 "+str(sys.argv[0])+ " status -Set or Not?"
    exit(0)



#Runs only if called
if __name__ == "__main__":

    if os.geteuid() != 0:
        print "\nYou need to have root privileges.\n Exiting...\n"
        exit(0)

    if len(sys.argv) < 2:
        print_usage()


    my = myEduroam()

    if sys.argv[1] == 'set':
        my.scan_air()
        my.show_5ghz()

        if my.pick_best():
            my.set_cell()
            my.force_disconnect()
            sleep(1)
            #my.restart_NM()
            my.force_connect()
        else:
            "No 5Ghz Cells Around"

    elif sys.argv[1] == 'unset':
        my.unset_cell()
        my.force_disconnect()
        #sleep(1)
        #my.restart_NM()
        my.force_connect()


    elif sys.argv[1] == 'status':
        mac = my.status_cell()
        if mac:
            print "\t Set to "+str(mac)
        else:
            print "\t Is in Auto"

    else:
        print_usage()
