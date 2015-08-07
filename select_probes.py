#!/usr/bin/env python
import urllib2
import json
import sys
import argparse
from collections import Counter
import pprint
from math import radians, cos, sin, asin, sqrt
'''
RIPE Atlas probe selection utility
'''

def parse_probe_json(d,pinfo,includedownprobes):
   for obj in d['objects']:
      # only consider connected-probes
      if not includedownprobes and (not obj['status'] or obj['status'] != 1): continue
      pinfo.append( { # maybe just append the obj itself?
         'id': obj['id'],
         'lat': obj['latitude'],
         'lon': obj['longitude'],
         'asn_v4': obj['asn_v4'],
         'asn_v6': obj['asn_v6'],
         'prefix_v4': obj['prefix_v4'],
         'prefix_v6': obj['prefix_v6'],
         'status': obj['status'],
         'is_public': obj['is_public'],
         'country_code': obj['country_code']
      })


## cache probe_info if needed
probe_info=None

def flush_cache():
   '''
   reinitialize the probe_list
   '''
   global probe_info
   probe_info=None

def getprobeinfo(includedownprobes=False):
   global probe_info
   if probe_info:
      return probe_info
   try:
      # status=1 = connected probes only
      base_url = 'https://atlas.ripe.net/'
      #url = "%s/api/v1/probe/?limit=100" % ( base_url )
      url = "%s/api/v1/probe-archive/?format=json" % ( base_url )
      req = urllib2.Request(url)
      req.add_header("Content-Type", "application/json")
      req.add_header("Accept", "application/json")
      conn = urllib2.urlopen(req)
      probe_data_batch = json.load(conn)
      pinfo = []
      parse_probe_json(probe_data_batch,pinfo,includedownprobes)
      while True:
         if not 'meta' in probe_data_batch: break 
         if not 'next' in probe_data_batch['meta']: break
         if probe_data_batch['meta']['next'] == None: break
         next_url = "%s%s" % (base_url,probe_data_batch['meta']['next'])
         next_req = urllib2.Request(next_url)
         next_req.add_header("Content-Type", "application/json")
         next_req.add_header("Accept", "application/json")
         next_conn = urllib2.urlopen(next_req)
         probe_data_batch = json.load(next_conn)
         parse_probe_json(probe_data_batch,pinfo,includedownprobes)
      probe_info=pinfo
      return pinfo
   except:
      print "couldn't get probe list %s " % ( sys.exc_info() )

def locstr2latlng( locstring ):
   try:
      locstr = urllib2.quote( locstring )
      geocode_url = "http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false" % locstr
      req = urllib2.urlopen(geocode_url)
      resp = json.loads(req.read())
      ll = resp['results'][0]['geometry']['location']
      return ( ll['lat'], ll['lng'] )
   except:
      print "could not determine lat/long for '%s'" % ( locstring )

def haversine(lat1, lon1, lat2, lon2):
    """
    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    return km 

def select_closest_to( tlat, tlon, count=10):
   prbinfo = getprobeinfo()
   for idx,p in enumerate(prbinfo):
      prbinfo[idx]['dist_km'] = haversine( tlat,tlon,p['lat'],p['lon'] )
   sel_probes = sorted(prbinfo, key=lambda x: x['dist_km'])[:count]
   return sel_probes

def select_within_radius( tlat, tlon, radius):
   prbinfo = getprobeinfo()
   for idx,p in enumerate(prbinfo):
      prbinfo[idx]['dist_km'] = haversine( tlat,tlon,p['lat'],p['lon'] )
   sel_probes = [i for i in prbinfo if i['dist_km'] <= radius]
   return sel_probes

def handle_args( args ):
   if args.radius and args.number:
      print "ERROR: can't use radius and number at the same time"
#   try:
   tlat=None
   tlon=None
   if args.locstring:
      tlat,tlon = locstr2latlng( args.locstring )
   elif args.point:
      tlat,tlon = args.point.split(',')
      tlat=float(tlat)
      tlon=float(tlon)
   prbinfo = getprobeinfo(includedownprobes=args.includedownprobes)
   for idx,p in enumerate(prbinfo):
      prbinfo[idx]['dist_km'] = haversine( tlat,tlon,p['lat'],p['lon'] )
   # now we have the prbinfo we need
   prbinfo = sorted(prbinfo, key=lambda x: x['dist_km'])
   sel_probes = []
   if args.radius:
      if args.maxperas:
         ascounter=Counter()
         for prb in prbinfo:
            if prb['dist_km'] < args.radius and ascounter[ prb['asn_v4' ] ] < args.maxperas:
               sel_probes.append( prb )
               ascounter[ prb['asn_v4'] ] += 1
      else:
         sel_probes = [i for i in prbinfo if i['dist_km'] <= args.radius]
   if args.number:
      if args.maxperas:
         ascounter=Counter()
         for prb in prbinfo:
            if ascounter[ prb['asn_v4'] ] < args.maxperas:
               sel_probes.append( prb )
               ascounter[ prb['asn_v4'] ] += 1
               #print "counter for %s is now %d (%d)" % ( prb['asn_v4'], ascounter[ prb['asn_v4'] ], args.maxperas )
               if len( sel_probes ) >= args.number:
                  break
      else:
         #sel_probes = sorted(prbinfo, key=lambda x: x['dist_km'])[:args.number ]
         sel_probes = prbinfo[:args.number]

   if args.fields:
      fields = args.fields.split(',')
      for p in sel_probes:
         pr_fields = []
         for f in fields:
            if f in p:
               pr_fields.append( str(p[f]) )
            else:
               pr_fields.append( None )
         print "%s" % ( '\t'.join( map(str,pr_fields )) )
   else:
      for p in sel_probes:
         print "%s" % ( p )
#   except:
#      print "ERROR: could not handle arguments: %s" % ( sys.exc_info() )

      
if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument('-v','--verbosity', action="count",default=0)
   parser.add_argument('-l','--locstring', help="location string, ie 'Amsterdam,NL'")
   parser.add_argument('-p','--point', help="location as <lat>,<lon>-string, ie '48.45,9.16'")
   parser.add_argument('-r','--radius', help="radius (km) within which to select probes", type=float)
   parser.add_argument('-n','--number', help="number of probes requested", type=int)
   parser.add_argument('-f','--fields', help="comma separated list of fields to return (output is tsv)")
   parser.add_argument('-a','--maxperas', help="maximum no. of probes per IPv4 source AS", type=int)
   parser.add_argument('-d','--includedownprobes', help="include probes that are down (default: don't include these)", action='store_true', default=False)
   args = parser.parse_args()
   handle_args( args )
