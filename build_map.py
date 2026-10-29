"""
Builds the North America basemap paths used inline in ballpark-tracker.html.

Inputs (Natural Earth 1:50m GeoJSON, public domain), downloaded next to this script:
  B=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson
  for f in ne_50m_admin_0_countries ne_50m_admin_1_states_provinces_lakes ne_50m_lakes; do
    curl -sfL -o $f.json $B/$f.geojson; done
Requires: pip install shapely

Output: paths.json with four SVG path strings (land, states, borders, lakes) for a
1000x580 viewBox. These were pasted into the <path d="..."> elements of the page.
The projection (Albers equal-area, parallels 29.5/45.5, origin 37.5N 96W, R=1000,
offset +500,+320) MUST match the project() function in the page's script, or pins
will land in the wrong place.
"""
import json, math
from shapely.geometry import shape, box, mapping
from shapely.ops import transform, unary_union

# Albers equal-area conic, same constants are used in the page's JS
R=1000; lat1,lat2,lat0,lon0 = map(math.radians,(29.5,45.5,37.5,-96))
n=(math.sin(lat1)+math.sin(lat2))/2; C=math.cos(lat1)**2+2*n*math.sin(lat1)
rho0=R*math.sqrt(C-2*n*math.sin(lat0))/n
def proj(lon,lat):
    l,p=math.radians(lon),math.radians(lat)
    rho=R*math.sqrt(C-2*n*math.sin(p))/n; th=n*(l-lon0)
    return rho*math.sin(th), -(rho0-rho*math.cos(th))
def pt(x,y,z=None):
    import numpy as np
    xs,ys=zip(*[proj(a,b) for a,b in zip(x,y)]); return xs,ys

# frame
corners=[proj(-125,24),proj(-66,24),proj(-128,51),proj(-62,51),proj(-96,22),proj(-96,52)]
print(corners)

W,H,OX,OY=1000,580,500,320
frame=box(0,0,W,H)
def tf(g):
    g=transform(lambda x,y,z=None:tuple(zip(*[(proj(a,b)[0]+OX,proj(a,b)[1]+OY) for a,b in zip(x,y)])), g)
    return g.buffer(0)
def to_path(g,tol=0.8):
    g=g.intersection(frame).simplify(tol,preserve_topology=True)
    if g.is_empty: return ''
    out=[]
    polys = [g] if g.geom_type=='Polygon' else [p for p in getattr(g,'geoms',[]) if p.geom_type=='Polygon']
    for p in polys:
        if p.area<4: continue
        from shapely.geometry import Polygon as P
        for ring in [p.exterior,*[r for r in p.interiors if P(r).area>40]]:
            c=list(ring.coords)
            if len(c)<4: continue
            out.append('M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in c[:-1])+'Z')
    return ''.join(out)
def lines_path(g,tol=0.8):
    g=g.intersection(frame).simplify(tol)
    segs=[]
    for l in (getattr(g,'geoms',[g])):
        if l.geom_type in('LineString',) and l.length>1:
            segs.append('M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in l.coords))
        elif l.geom_type=='MultiLineString':
            for s in l.geoms: segs.append('M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in s.coords))
    return ''.join(segs)

bbox_ll=box(-140,10,-50,62)
countries=json.load(open('ne_50m_admin_0_countries.json'))['features']
land=[]; cmap={}
for f in countries:
    g=shape(f['geometry'])
    if not g.intersects(bbox_ll): continue
    g=tf(g.intersection(bbox_ll).buffer(0))
    land.append(g); cmap[f['properties']['ADM0_A3']]=g
land_u=unary_union(land)
# national borders = boundaries shared between countries
borders=unary_union([a.boundary for a in land]).difference(land_u.boundary.buffer(0.5))
states=[f for f in json.load(open('ne_50m_admin_1_states_provinces_lakes.json'))['features'] if f['properties']['adm0_a3'] in('USA','CAN')]
sg=[tf(shape(f['geometry']).intersection(bbox_ll).buffer(0)) for f in states]
inner=unary_union([g.boundary for g in sg]).difference(land_u.boundary.buffer(0.6)).difference(borders.buffer(0.6))
lakes=[tf(shape(f['geometry']).buffer(0)) for f in json.load(open('ne_50m_lakes.json'))['features'] if shape(f['geometry']).intersects(bbox_ll) and f['properties'].get('scalerank',9)<=2]
out={'land':to_path(land_u),'borders':lines_path(borders),'states':lines_path(inner),'lakes':to_path(unary_union(lakes))}
for k,v in out.items(): print(k,len(v))
json.dump(out,open('paths.json','w'))
