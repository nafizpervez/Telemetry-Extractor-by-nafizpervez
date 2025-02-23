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

    # Frame Center Latitude/Longitude/Elevation
    merged_df["Frame Center Latitude"] = merged_df["GPS (Lat.) [deg]"]
    merged_df["Frame Center Longitude"] = merged_df["GPS (Long.) [deg]"]
    merged_df["Frame Center Elevation"] = merged_df["GPS (Alt.) [m]"]

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

    # Platform Heading Angle (integrating gyroscope z-axis angular velocity)
    merged_df["Platform Heading Angle"] = np.cumsum(merged_df["Gyroscope (z) [rad/s]"])

    # Platform Ground Speed (from GPS 2D speed)
    merged_df["Platform Ground Speed"] = merged_df["GPS (2D speed) [m/s]"]

    # Platform True Airspeed (from GPS 3D speed)
    merged_df["Platform True Airspeed"] = merged_df["GPS (3D speed) [m/s]"]

    # Platform Vertical Speed (from change in GPS altitude)
    merged_df["Platform Vertical Speed"] = (
        merged_df["GPS (Alt.) [m]"].diff() / merged_df["Precision Timestamp"].diff()
    )

    # Slant Range (from GPS altitude and horizontal distance)
    merged_df["Slant Range"] = np.sqrt(
        (merged_df["GPS (Alt.) [m]"] ** 2) + (merged_df["GPS (2D speed) [m/s]"] ** 2)
    )

    # Wind Speed and Wind Direction (using GPS 2D speed and heading)
    merged_df["Wind Speed"] = np.sqrt(
        (merged_df["Platform Ground Speed"] ** 2)
        - (merged_df["GPS (2D speed) [m/s]"] ** 2)
    )
    merged_df["Wind Direction"] = np.degrees(
        np.arctan2(merged_df["GPS (Lat.) [deg]"], merged_df["GPS (Long.) [deg]"])
    )

    # Platform Magnetic Heading (using Gyroscope + Accelerometer data)
    merged_df["Platform Magnetic Heading"] = np.degrees(
        np.arctan2(
            merged_df["Gyroscope (y) [rad/s]"], merged_df["Gyroscope (x) [rad/s]"]
        )
    )

    # Sensor North Velocity and Sensor East Velocity (from GPS 2D speed)
    merged_df["Sensor North Velocity"] = merged_df["GPS (2D speed) [m/s]"] * np.sin(
        np.radians(merged_df["GPS (Lat.) [deg]"])
    )
    merged_df["Sensor East Velocity"] = merged_df["GPS (2D speed) [m/s]"] * np.cos(
        np.radians(merged_df["GPS (Long.) [deg]"])
    )

    # Assign FOV values based on GoPro Hero6 Black specs (Wide FOV)
    merged_df["Sensor Horizontal Field of View"] = 122.0  # Wide FOV in degrees
    merged_df["Sensor Vertical Field of View"] = 94.0  # Wide FOV in degrees

    # Select required columns for output
    output_columns = [
        "Precision Timestamp",
        "Sensor Latitude",
        "Sensor Longitude",
        "Sensor Ellipsoid Height",
        "Sensor True Altitude",
        "Frame Center Latitude",
        "Frame Center Longitude",
        "Frame Center Elevation",
        "Platform Pitch Angle",
        "Platform Roll Angle",
        "Sensor Relative Roll Angle",
        "Sensor Relative Elevation Angle",
        "Sensor Relative Azimuth Angle",
        "Sensor Horizontal Field of View",
        "Sensor Vertical Field of View",
        "Platform Heading Angle",
        "Platform Ground Speed",
        "Platform True Airspeed",
        "Platform Vertical Speed",
        "Slant Range",
        "Wind Speed",
        "Wind Direction",
        "Platform Magnetic Heading",
        "Sensor North Velocity",
        "Sensor East Velocity",
    ]

    # Create final output dataframe
    output_df = merged_df[output_columns]

    # Save to CSV
    output_df.to_csv(output_file, index=False)
    print(f"ArcGIS GoPro Telemetry Data saved to {output_file}")


# Example usage:
# Provide paths to the accelerometer, GPS, and gyroscope data files, and the desired output file name
accel_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/GX019029_telemetry_data_ACCL.csv"
gps_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/GX019029_telemetry_data_GPS5.csv"
gyro_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/GX019029_telemetry_data_GYRO.csv"
output_file = "D:/Office_Projects/Local_Projects/LGED_solution_scripts/telemetry_extractor_by_NafizPervez_D_12_Feb_25/sample_csv/outFile_combined.csv"

process_telemetry_data(accel_file, gps_file, gyro_file, output_file)
