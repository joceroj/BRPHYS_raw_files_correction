# Correction of raw files collected @ BRPHYS --> Bristol campaign

This tool has been developed to make corrections on the raw files collected by system No. 18 during the field campaign at Bristol.
All files collected using the velocity-azimuth display (VAD) and vertical stare techniques need this correction.

# How to use it?

This tool only works for files collected by Halo-photonics lidars. It is required:

1) Raw `*.hpl` files -> VAD (Doppler velocity)
2) Processed `*.hpl` files -> VAD (Horizontal wind profile,i.e., wind speed and wind direction)
3) Raw `*.hpl` files -> Stare (Doppler velocity)
4) Background files `*.txt` -> Stare

### Running the code

Currently, this tool is useful to apply corrections to all `*.hpl` files found in the University of Reading server, in the following path:

`input_path = /storage/research/actual01/disk1/urban/obs/LiDAR/Bristol/BRPHYS`

Output files are stored in:

`outputh_path = /storage/research/actual01/disk1/urban/obs/LiDAR/Bristol/BRPHYS_co`

This repository has three scripts to correct every type of `*.hpl` files:

1) `BRPHYS_VAD_Stare_Correction.py` is useful to correct Raw `*.hpl` files -> VAD and Stare. Type the following in the terminal:
```
cd existing_repo
python BRPHYS_VAD_Stare_Correction.py --prefix Wind
python BRPHYS_VAD_Stare_Correction.py --prefix Stare
```

2) `BRPHYS_Processed_Correction.py` is useful to correct Processed `*.hpl` files -> VAD. Type the following in the terminal:
```
cd existing_repo
python BRPHYS_Processed_Correction.py
```

