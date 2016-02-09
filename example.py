import urllib2

p = urllib2.urlopen("http://www.google.com")
c = p.read()
print c

