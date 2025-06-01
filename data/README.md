# VeriGreen Data Directory

This directory contains satellite imagery and processed data for the VeriGreen project.

## Directory Structure

```
data/
├── raw/              # Original downloaded data
│   └── sentinel/     # Sentinel-2 satellite imagery
│       ├── B04.jp2   # Red band (10m resolution)
│       └── B08.jp2   # NIR band (10m resolution)
└── processed/        # Processed outputs
    ├── tiles/        # 32x32 pixel tiles (coming soon)
    └── ndvi/         # NDVI calculations (coming soon)
```

## Important Note

**Data files are not stored in Git!**

This is because:

- Satellite imagery files are large (80MB+ each)
- Binary files don't benefit from version control
- Data can be regenerated using download scripts

## Downloading Data

To download the required Sentinel-2 imagery:

```bash
cd backend
./scripts/download_data.sh
```

This will download the satellite imagery for Sabangau National Park:

- **Tile**: 49MCT (Central Kalimantan, Indonesia)
- **Date**: May 1, 2023 (cloud-free)
- **Bands**: B04 (Red) and B08 (NIR)
- **Resolution**: 10m per pixel
- **Size**: ~160MB total

## Data Source

Data is downloaded from the AWS S3 public bucket:

- Bucket: `s3://sentinel-s2-l2a/`
- No authentication required (public data)
