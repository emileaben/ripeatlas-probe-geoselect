# ripeatlas-probe-geoselect

Tool to select probes based on a (city) location

    usage: select_probes.py [-h] [-v] [-l LOCSTRING] [-p POINT] [-r RADIUS]
    [-n NUMBER] [-f FIELDS] [-a MAXPERAS] [-d]
    
    -h, --help            show this help message and exit
    -v, --verbosity
    -l LOCSTRING, --locstring LOCSTRING
                        location string, ie 'Amsterdam,NL'
    -p POINT, --point POINT
                     location as <lat>,<lon>-string, ie '48.45,9.16'
    -r RADIUS, --radius RADIUS
                      radius (km) within which to select probes
    -n NUMBER, --number NUMBER
                     number of probes requested
    -f FIELDS, --fields FIELDS
                     comma separated list of fields to return (output is
                     tsv)
    -a MAXPERAS, --maxperas MAXPERAS
                     maximum no. of probes per IPv4 source AS
    -d, --includedownprobes
                      include probes that are down (default: don't include
                      these)

Example usage: Select probes in a radius of 20 km from the city center of the city of Maastricht in the Netherlands

    ./select_probes.py -l "Maastricht,NL" -r 20 -f id,asn_v4

Output for that example has tab separated list of probe ID and IPv4 ASNs.
