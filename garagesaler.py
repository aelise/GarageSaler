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

#temp imports for dev and debug
import json
import pdb


class Sale(object):
    """Base class for sale objects.
       Each inheriting class needs to define the function sale_info
    """
    homeaddr = None
    homelat = None
    homelng = None
    gmaps_apikey = None

    def __init__(self, text):
        # Init vars
        self.rawtext = text
        self.straddress = None
        self.url = None
        self.happeningnow = None
        self.pictures = None
        self.distancetohome = None
        self.lat = None
        self.lng = None

        # Populate vars
        self.sale_info(text)

    def formatted_address(self, addy):
        addy = addy.replace('<br/>','+')
        return addy.strip().strip(',').strip('.').replace(' ', '+')

    def getlatlng(self, address):
        g = goo.Client(key=self.gmaps_apikey)
        ll = g.geocode(address, components={'country':'US'})
        return (ll[0]['geometry']['location']['lat'], \
                ll[0]['geometry']['location']['lng'])

    def getdist2home(self):
        g = goo.Client(key=self.gmaps_apikey)
        distmat = g.distance_matrix(self.homeaddr, self.straddress, \
                                    mode='walking')
        self.distancetohome = distmat['rows'][0]['elements'][0]['distance']['value']
        return self.distancetohome


class EstateSale(Sale):
    """Class to collect and contain information on Estate Sales
       from EstateSales.net
    """
    def sale_info(self, es):
        now = es.select('span.timeMessage')
        if not now:
            return None

        ur = es.select('h3 > a')
        street = es.find('div',attrs={'id':re.compile('.*PrintableAddress.*')})
        if not ur or not street:
            print "Whoops"
            return None

        if street.text != '':
            self.straddress = self.formatted_address(street.text)
            (self.lat, self.lng) = self.getlatlng(self.straddress)
            self.getdist2home()
        self.url   = 'http://www.estatesales.net' + ur[0]['href']
        self.happeningnow = now[0].text


class GarageSale(Sale):
    """Class to collect and contain information on Garage Sales from
       craigslist.com
    """
    def sale_info(self, gs):
        pass #tbd

def plotsalemap(saleslist, apikey, home):
    """Plot all sales in saleslist using the static google maps API
       Returns url for API request
    """

    baseurl = 'https://maps.googleapis.com/maps/api/staticmap?'

    if isinstance(saleslist[0], basestring):
        markers = ['color:blue|label:S|' + x for x in saleslist if x != '']
    else:
        markers = ['color:blue|label:S|' + str(x[0]) + ',' + str(x[1]) \
                    for x in saleslist if x != '']

    myparams = {'key': [apikey],
                'markers': ['color:red|label:H|' + home] + markers,
                'maptype': ['roadmap'],
                'size': ['600x300']}

    new = requests.get(baseurl, params=myparams)
    return new.url

def plotroute(saleslist, apikey, home):
    """ Plots optimal route in google static map
        TODO: return text turn-by-turn directions
    """
    baseurl = plotsalemap(saleslist, apikey, home)

    # get optimal route from Google
    route = goo.Client(apikey).directions(home, home, mode='walking', \
                                          waypoints=saleslist, \
                                          optimize_waypoints='True')

    #get encoded polyline from route, put it in myparams = {'enc' : polyline}
    myparams = {'path' : 'weight:3|color:navy|enc:' + \
                         route[0]['overview_polyline']['points']}
    new = requests.get(baseurl, params=myparams)
    return new.url


def getwalkingroute(apikey, home, sales, triplength):
    """ Returns a list of waypoints in an optimal walking route
        which starts and ends at the users home address (home).
    """
    g = goo.Client(apikey)

    # drop sales greater than (triplength) miles away from home
    wp = np.array([(es.lat, es.lng, es.distancetohome) for es in sales \
                         if es.lat is not None
                         and es.distancetohome < triplength])

    # If more than 8 waypoints remaining, choose the 8 closest to home
    if len(wp)>8:
        wp = wp[wp[:,2].argsort()]
        wp = wp[0:8,:]

    # get directions. if total distance greater than triplength, drop
    # farthest stop and try again
    bestroute = False
    while not bestroute:
        time.sleep(2)
        route = g.directions(home, home, mode='walking', \
                             waypoints=wp[:,0:2].tolist(), \
                             optimize_waypoints='True')
        temptriplen = sum([i['distance']['value'] for i in route[0]['legs']])
        if temptriplen > 2*triplength:
            wp = wp[wp[:,2]<max(wp[:,2])]
            print wp
        else:
            bestroute = True

    return wp


def getdata():
    r = requests.get('http://www.estatesales.net/GA/Decatur/30033')
    soup = BeautifulSoup(r.text,'html5lib')
    sales = soup.find_all('section', attrs={'class':'saleItem'})
    return sales

def main():
    """ """
    sales = getdata()

    # Get user-specific values from file
    with open('user_values.txt') as myfile:
        Gstaticmap_apikey = myfile.readline().rstrip()
        Sale.gmaps_apikey = myfile.readline().rstrip()
        Sale.homeaddr = myfile.readline().rstrip()

    # Get current sales and update location
    sale_info_list = [EstateSale(e) for e in sales]

    # Update home info
    if Sale.homelat is None:
        (Sale.homelat, Sale.homelng) = \
                sale_info_list[0].getlatlng(Sale.homeaddr)

    # Get walking route from home to sale(s) and back home
    waypoints = getwalkingroute(Sale.gmaps_apikey, Sale.homeaddr, \
                                sale_info_list, 17000)

    # Plot all sales within walking distance
    myurl = plotsalemap(waypoints.tolist(), Gstaticmap_apikey, Sale.homeaddr)
    webbrowser.open(myurl)

    # Plot walking route
    myurl = plotroute(waypoints[:3,0:2].tolist(), Gstaticmap_apikey, Sale.homeaddr)
    webbrowser.open(myurl)


if __name__ == '__main__':
    main()