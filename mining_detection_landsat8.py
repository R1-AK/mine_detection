# --- Install and import ---
!pip install earthengine-api geemap geopandas --quiet
import ee, geemap, geopandas as gpd, json

# --- Authenticate ---
service_account = 'your-service-account@your-project.iam.gserviceaccount.com'
key_file = 'path/to/your-service-account-key.json'
ee.Initialize(ee.ServiceAccountCredentials(service_account, key_file))
print("✅ Earth Engine authenticated")

# --- Load Lease Shapefile ---
shp_path = "path/to/your/Lease_Maluku.shp"
gdf = gpd.read_file(shp_path).to_crs(epsg=4326)
lease_fc = ee.FeatureCollection(json.loads(gdf.to_json()))
center = gdf.to_crs(gdf.estimate_utm_crs()).geometry.centroid.to_crs(4326)
center_lat, center_lon = center.y.mean(), center.x.mean()

# --- Landsat 8 Surface Reflectance ---
def mask_l8(image):
    qa = image.select('QA_PIXEL')
    cloud = (1 << 3)
    shadow = (1 << 4)
    mask = qa.bitwiseAnd(cloud).eq(0).And(qa.bitwiseAnd(shadow).eq(0))
    return image.updateMask(mask).select(['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'])\
               .multiply(0.0000275).add(-0.2)

l8 = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
      .filterBounds(lease_fc)
      .filterDate('2021-01-01', '2023-12-31')
      .filter(ee.Filter.lt('CLOUD_COVER', 30))
      .map(mask_l8)
      .median())

# --- Terrain data ---
dem = ee.Image('USGS/SRTMGL1_003').clip(lease_fc)
slope = ee.Terrain.slope(dem)
elevation = dem

# --- Compute relative depth ---
z_stats = elevation.reduceRegion(
    reducer=ee.Reducer.percentile([5, 95]),
    geometry=lease_fc.geometry(),
    scale=90,
    bestEffort=True,
    maxPixels=1e7
)
min_elev = ee.Number(z_stats.get('elevation_p5'))
max_elev = ee.Number(z_stats.get('elevation_p95'))
depth = ee.Image.constant(max_elev).subtract(elevation).rename('Depth')

# --- Spectral Indices ---
ndvi = l8.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
ndbi = l8.normalizedDifference(['SR_B6', 'SR_B5']).rename('NDBI')
bsi = l8.expression(
    '((R + SWIR1) - (NIR + B)) / ((R + SWIR1) + (NIR + B))',
    {
        'R': l8.select('SR_B4'),
        'B': l8.select('SR_B2'),
        'NIR': l8.select('SR_B5'),
        'SWIR1': l8.select('SR_B6')
    }).rename('BSI')

# --- Combine spectral + terrain criteria ---
mask = (
    ndvi.lt(0.4)
    .And(bsi.gt(0.0))
    .And(ndbi.gt(-0.1))
    .And(slope.gt(10))
    .And(depth.gt(20))
).selfMask()

# --- Morphological Operation: Dilation using focal_max ---
kernel = ee.Kernel.square(radius=60, units='meters')
morph_mask = mask.focal_max(kernel=kernel, iterations=1).selfMask()

# --- Map Display ---
Map = geemap.Map(center=[center_lat, center_lon], zoom=12)
Map.add_basemap('SATELLITE')
Map.addLayer(lease_fc, {'color': 'yellow'}, 'Lease Area')
Map.addLayer(morph_mask, {'palette': ['red']}, 'Mining Mask (Dilation)')

# --- Convert to vectors ---
vectors = morph_mask.reduceToVectors(
    geometry=lease_fc.geometry(),
    scale=30,
    geometryType='polygon',
    bestEffort=True,
    maxPixels=1e7
).map(lambda f: f.set({'area': f.geometry().area(maxError=1)}))

# --- Filter polygons > 5000 m2 ---
mining_polygons = vectors.filter(ee.Filter.gte('area', 5000))

# --- Final raster from solid polygon ---
mining_mask = mining_polygons.reduceToImage(['area'], ee.Reducer.first()).gt(0).selfMask()
Map.addLayer(mining_mask, {'palette': ['orange']}, 'Final Mining Detected')

# --- Export to Drive ---
task = ee.batch.Export.table.toDrive(
    collection=mining_polygons,
    description='DEM_mining_detection_dilated',
    folder='GEE_exports',
    fileNamePrefix='mining_Maluku_L8_dilated',
    fileFormat='SHP'
)
task.start()
print("🚀 Export started to Google Drive > GEE_exports")
Map
