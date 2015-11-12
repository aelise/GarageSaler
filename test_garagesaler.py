import garagesaler
import numpy as np
import pdb
import pytest
import webbrowser

latlng = [(33.9664069, -84.695144), (33.830151, -84.364142),
    (33.878717, -84.100219), (33.603503, -84.088714), (33.877504, -84.102704),
    (33.847655, -83.968959), (33.971314, -84.234938), (33.886925, -84.021199),
    (33.80473500000001, -84.18624299999999), (34.122225, -84.338312),
    (33.950643, -84.38534500000002), (33.521759, -84.22009),
    (33.987926, -84.410889),(33.891504, -84.37335),
    (33.99309, -84.60245599999999), (33.480858, -84.156187),
    (34.008382, -84.465389), (33.988097, -84.28012199999999),
    (33.8627309, -84.14552599999999),(33.873852, -84.05530300000001),
    (34.062118, -84.54476199999999), (33.7004018, -84.56904540000001),
    (33.985647, -84.140019), (33.657656, -83.910207), (34.056326, -84.5589509),
    (33.978094, -84.365219),(33.929829, -84.36549699999999),
    (34.023923, -84.612082), (33.882965, -83.978917),(34.0118719, -84.190422)]

@pytest.fixture()
def userinfo_setup():
    # Get user-specific values from file
    with open('user_values.txt') as myfile:
        Gstaticmap_apikey = myfile.readline().rstrip()
        gmaps_apikey = myfile.readline().rstrip()
        homeaddr = myfile.readline().rstrip()
    return [gmaps_apikey, homeaddr]


def test_plotroute(userinfo_setup):
    u = garagesaler.plotroute(latlng[:3], userinfo_setup[0], userinfo_setup[1])
    assert webbrowser.open(u)

