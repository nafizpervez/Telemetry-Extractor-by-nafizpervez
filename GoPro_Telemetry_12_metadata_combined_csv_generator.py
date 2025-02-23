import pandas as pd
import numpy as np


def process_telemetry_data(accel_file, gps_file, gyro_file, output_file):
    # Load input files
    accel_df = pd.read_csv(accel_file)
    gps_df = pd.read_csv(gps_file)
    gyro_df = pd.read_csv(gyro_file)

    # Check if 'date' column exists in all dataframes and handle missing columns
    if "date" not in gps_df.columns:
        raise KeyError("The GPS data file does not contain a 'date' column.")
    if "date" not in accel_df.columns:
        raise KeyError("The Accelerometer data file does not contain a 'date' column.")
    if "date" not in gyro_df.columns:
        raise KeyError("The Gyroscope data file does not contain a 'date' column.")

    # Merge dataframes on the 'date' column
    merged_df = gps_df.merge(gyro_df, on="date", how="outer")
    merged_df = merged_df.merge(accel_df, on="date", how="outer")

    # Convert timestamp to a Unix timestamp in microseconds
    merged_df["Precision Timestamp"] = (
        pd.to_datetime(merged_df["date"]).astype("int64") // 10**3
    )

    # Map existing columns to required fields
    merged_df["Sensor Latitude"] = merged_df["GPS (Lat.) [deg]"]
    merged_df["Sensor Longitude"] = merged_df["GPS (Long.) [deg]"]
    merged_df["Sensor Ellipsoid Height"] = merged_df["GPS (Alt.) [m]"]
    merged_df["Sensor True Altitude"] = merged_df["GPS (Alt.) [m]"]

    # Calculate Platform Pitch and Roll Angles using accelerometer data
    merged_df["Platform Pitch Angle"] = np.degrees(
        np.arctan2(
            merged_df["Accelerometer (x) [m/s²]"],
            np.sqrt(
                merged_df["Accelerometer (y) [m/s²]"] ** 2
                + merged_df["Accelerometer (z) [m/s²]"] ** 2
            ),
        )
    )

    merged_df["Platform Roll Angle"] = np.degrees(
        np.arctan2(
            merged_df["Accelerometer (y) [m/s²]"],
            np.sqrt(
                merged_df["Accelerometer (x) [m/s²]"] ** 2
                + merged_df["Accelerometer (z) [m/s²]"] ** 2
            ),
        )
    )

    # Relative angles from Gyroscope
    merged_df["Sensor Relative Roll Angle"] = merged_df["Gyroscope (x) [rad/s]"]
    merged_df["Sensor Relative Elevation Angle"] = merged_df["Gyroscope (y) [rad/s]"]
    merged_df["Sensor Relative Azimuth Angle"] = merged_df["Gyroscope (z) [rad/s]"]

    # Assign FOV values based on GoPro Hero6 Black specs (Wide FOV)
    merged_df["Sensor Horizontal Field of View"] = 122.0  # Wide FOV in degrees
    merged_df["Sensor Vertical Field of View"] = 94.0  # Wide FOV in degrees

    # Select required columns
    output_columns = [
        "Precision Timestamp",
        "Sensor Latitude",
        "Sensor Longitude",
        "Sensor Ellipsoid Height",
        "Sensor True Altitude",
        "Platform Pitch Angle",
        "Platform Roll Angle",
        "Sensor Relative Roll Angle",
        "Sensor Relative Elevation Angle",
        "Sensor Relative Azimuth Angle",
        "Sensor Horizontal Field of View",
        "Sensor Vertical Field of View",
    ]

    # Create final output dataframe
    output_df = merged_df[output_columns]

    # Save to CSV
    output_df.to_csv(output_file, index=False)
    print(f"ArcGIS GoPro Telemetry Data saved to {output_file}")


# Example usage:
# Provide paths to the accelerometer, GPS, and gyroscope data files, and the desired output file name
accel_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/GX019027_telemetry_data_ACCL.csv"
gps_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/GX019027_telemetry_data_GPS5.csv"
gyro_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/GX019027_telemetry_data_GYRO.csv"
output_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/outFile_combined_GX019027.csv"

process_telemetry_data(accel_file, gps_file, gyro_file, output_file)
