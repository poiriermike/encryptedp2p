import os,re

# Run me after doing a fab get_ip. It will condense all of the Ip's into a single file: ip.txt
# then it will go to each node and produce a text file called neighbours.txt that will contain all ips with
# the exception of that node.

with open("ips.txt", "w") as f:
    pass
with open("ips.txt", "a") as f:
    for dir in os.listdir("."):
        if os.path.isdir(dir):
            if os.path.isfile(dir + "/myip.txt"):
                print("ip.txt found in" + dir)
                with open(dir + "/myip.txt", "r") as g:
                    txt = g.readline()
                    result = re.search("10\.\d*\.\d*\.\d*", str(txt))
                    f.write(str(result.group(0) + "\n"))

print("-------------------------------")
for dir in os.listdir("."):
    if os.path.isfile(dir + "/myip.txt"):
        with open(dir + "/neighbours.txt", "w") as n:
            with open(dir + "/myip.txt", "r") as g:
                me = g.readline()
                with open("ips.txt", "r") as f:
                    for ip in f:
                        if not re.search(str(ip.split()[0]), str(me)):
                            print("Adding " + ip.split()[0] + " to " + dir + "/neighbours.txt")
                            n.write(ip)