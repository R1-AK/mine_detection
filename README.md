# 🪨 Mining Detection using Landsat 8 and DEM in Google Earth Engine

## 🧭 Context & Motivation

Mining activities can cause substantial environmental degradation, especially when operations expand beyond their permitted lease boundaries. Unfortunately, manual delineation of mine extents is labor-intensive, inconsistent, and difficult to scale. Moreover, official mining lease shapefiles may not reflect the full spatial impact of mining operations, particularly in areas with limited monitoring or regulatory oversight.

This script addresses these challenges by providing an automated, scalable method to detect potential mining areas using multi-year Landsat 8 surface reflectance imagery, terrain data, and spectral indices, all processed through Google Earth Engine (GEE). By combining vegetation and soil indicators with topographic context, the method helps identify land disturbances likely related to mining. It is especially valuable for researchers, government agencies, and civil society organizations focused on **land use monitoring, environmental compliance, and resource governance**.

## 📌 Features

- Authenticates with Google Earth Engine via service account  
- Loads and displays mining lease shapefile  
- Filters and masks cloud-free **Landsat 8 SR** imagery (2021–2023)  
- Computes terrain attributes: elevation, slope, and relative depth  
- Calculates spectral indices: NDVI, NDBI, BSI  
- Applies a multi-criteria mask to detect likely mining land use  
- Enhances the mask with **morphological dilation**  
- Converts raster mask to **polygon vector**  
- Filters polygons by area > 5000 m²  
- Visualizes results with `geemap`  
- Exports shapefile to Google Drive  

## 🔧 Requirements

Install the required Python libraries:
pip install earthengine-api geemap geopandas


## 📂 Input Data

- **Shapefile** of mining leases (e.g. `Lease_Maluku.shp`)  
- **Google Earth Engine service account** and JSON key file  

## 🚀 How to Run

1. Replace your **GEE service account email** and **path to JSON key** in:

  service_account = 'your-service-account@project.iam.gserviceaccount.com'
  key_file = 'path/to/your-key.json'

2. Update the path to your **lease shapefile**:

  shp_path = "path/to/Lease_Maluku.shp"


3. Run the script in a Jupyter Notebook or Python environment.

## 🧠 Methodology

The detection is based on these criteria:

- **Low NDVI (< 0.4)** → sparse vegetation  
- **High BSI (> 0)** → exposed bare soil  
- **NDBI > -0.1** → built-up or disturbed land  
- **Slope > 10°** and **Relative Depth > 20 m** → terrain factors  
- **Morphological dilation** helps merge fragmented patches  

Only **solid polygons > 5000 m²** are retained and exported.

## 📤 Output

- Shapefile named `mining_Maluku_L8_dilated.shp` in your Google Drive under folder `GEE_exports`  
- Visual results displayed in an interactive map  

## 🗺️ Visualization

The map will display:
- 🟡 Yellow polygons: Lease boundary  
- 🔴 Red mask: Initial detected areas after morphological filtering  
- 🟠 Orange raster: Final solid mining detection  



