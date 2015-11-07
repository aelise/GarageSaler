from bs4 import BeautifulSoup
from collections import OrderedDict
import googlemaps as goo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import requests
from sklearn.cluster import KMeans
import time
import webbrowser


class Sale(object):
    """Base class for sale objects. Each inheriting class needs to define fn sale_info"""
    homeaddress = None
    homelat = None
    homelng = None
    gmaps_apikey = None

    def __init__(self, text):
        # Init vars
        self.rawtext = text
        self.streetaddress = None
        self.zipcode = None
        self.url = None
        self.happeningnow = None
        self.pictures = None
        self.distancetohome = None
        self.lat = None
        self.lng = None

        # Populate vars
        self.sale_info(text)

    def formatted_address(self, addy):
        return addy.strip().strip(',').strip('.').replace(' ', '+')

    def getlatlong(self, address):
        g = goo.Client(key=Sale.gmaps_apikey)
        print address
        ll = g.geocode(address, components={'country':'US'})
        return (ll[0]['geometry']['location']['lat'], ll[0]['geometry']['location']['lng'])


class EstateSale(Sale):
    """Class to collect and contain information on Estate Sales from EstateSales.net """
    def sale_info(self, es):
        now = es.select('span.timeMessage')
        if not now:
            return None

        ur = es.select('h3 > a')
        street = es.find('span',attrs={'id':re.compile('.*StreetAddressSpan.*')})
        zc = es.find('span',attrs={'id':re.compile('.*PostalCodeSpan.*')})
        if not ur or not street or not zc:
            print "Whoops"
            return None

        self.zipcode = zc.text
        if street.text != '' and self.zipcode is not None:
            self.streetaddress = self.formatted_address(street.text)
            (self.lat, self.lng) = self.getlatlong(self.streetaddress+','+self.zipcode)
        self.url   = 'http://www.estatesales.net' + ur[0]['href']
        self.happeningnow = now[0].text


class GarageSale(Sale):
    """Class to collect and contain information on Garage Sales from craigslist.com """
    def sale_info(self, gs):
        pass #tbd

def plotsalemap(saleslist, apikey, home):
    """ """
    baseurl = 'https://maps.googleapis.com/maps/api/staticmap?'

    if isinstance(saleslist[0], basestring):
        markers = ['color:blue|label:S|' + x for x in saleslist if x != '']
    else:
        markers = ['color:blue|label:S|' + str(x[0]) + ',' + str(x[1]) for x in saleslist if x != '']

    myparams = {'key': [apikey],
                'markers': ['color:red|label:H|' + home] + markers,
                'maptype': ['roadmap'],
                'size': ['600x300'],
                'center': [home] }

    new = requests.get(baseurl, params=myparams)
    webbrowser.open(new.url)
    return new.url

def plotroute(saleslist, apikey, home):
    """ Next TO DO: actually turn this into a function that plots (and prints) the route"""
    pass

def getwalkingroute(g, home, latlng, triplength):
    """ """
    # drop sales greater than (triplength) miles away from home
    distmat = g.distance_matrix(home, latlng, mode='walking')
    dist2home = np.array([x['distance']['value'] for x in distmat['rows'][0]['elements']])
    print dist2home
    latlng = np.array(latlng)
    wp = np.c_[ latlng[dist2home<(triplength)] ,
                   dist2home[dist2home<(triplength)] ]
    print wp[:,0:2].tolist()

    # If more than 8 waypoints remaining, choose the 8 closest to home
    if len(wp)>8:
        wp = wp[wp[:,2].argsort()]
        wp = wp[0:8,:]
        print wp[:,0:2].tolist()

    # get directions. if total distance greater than triplength, drop
    # farthest stop and try again
    bestroute = False
    while not bestroute:
        time.sleep(2)
        route = g.directions(home, home, mode='walking', waypoints=wp[:,0:2].tolist(), optimize_waypoints='True')
        print [i['distance']['value'] for i in route[0]['legs']]
        temptriplen = sum([i['distance']['value'] for i in route[0]['legs']])
        if temptriplen > 2*triplength:
            wp = wp[wp[:,2]<max(wp[:,2])]
            print wp
        else:
            bestroute = True

    return wp


def main():
    """ """
    r = requests.get('http://www.estatesales.net/GA/Decatur/30033')
    soup = BeautifulSoup(r.text,'html5lib')
    sales = soup.find_all('section', attrs={'class':'saleItem'})

    # Get user-specific values from file
    with open('user_values.txt') as myfile:
        Gstaticmap_apikey = myfile.readline().rstrip()
        Sale.gmaps_apikey = myfile.readline().rstrip()
        Sale.homeaddress = myfile.readline().rstrip()

    # Get current sales and update location
    sale_info_list = [EstateSale(e) for e in sales]

    # Update home info
    if Sale.homelat is None:
        (Sale.homelat, Sale.homelng) = sale_info_list[0].getlatlong(Sale.homeaddress)

    # Compile info in usable format for mapping
    latlongs_str = [(str(es.lat)+','+str(es.lng)) for es in sale_info_list if es.lat is not None]
    latlongs_tup = [(es.lat,es.lng) for es in sale_info_list if es.lat is not None]

    waypoints = getwalkingroute(goo.Client(Sale.gmaps_apikey), Sale.homeaddress, latlongs_tup, 17000)

    plotsalemap(latlongs_str[:30], Gstaticmap_apikey, Sale.homeaddress)
    plotsalemap(waypoints.tolist(), Gstaticmap_apikey, Sale.homeaddress)



if __name__ == '__main__':
    main()