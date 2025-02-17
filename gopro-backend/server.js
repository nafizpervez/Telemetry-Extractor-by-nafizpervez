const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const gpmfExtract = require("gpmf-extract");
const goproTelemetry = require("gopro-telemetry");
const fs = require("fs");
const { promisify } = require("util");
const writeFileAsync = promisify(fs.writeFile);

const app = express();
const port = 5000;

app.use(cors());

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/");
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ storage });

const downloadsDir = path.join(__dirname, "downloads");
if (!fs.existsSync(downloadsDir)) {
  fs.mkdirSync(downloadsDir);
}

app.post("/upload", upload.single("video"), async (req, res) => {
  const videoPath = req.file.path;
  const videoName = path.basename(
    req.file.originalname,
    path.extname(req.file.originalname)
  );

  try {
    // Create a read stream for the large video file
    const videoStream = fs.createReadStream(videoPath);

    // Use a temporary buffer to handle the video stream (if necessary for gpmfExtract)
    const chunks = [];
    for await (const chunk of videoStream) {
      chunks.push(chunk);
    }
    const fileBuffer = Buffer.concat(chunks);

    const extractedData = await gpmfExtract(fileBuffer);

    console.log("Length of data received:", extractedData.rawData.length);
    console.log(
      "Framerate of data received:",
      1 / extractedData.timing.frameDuration
    );

    const gpsData = await goproTelemetry(extractedData, {
      stream: "GPS5",
      repeatSticky: true,
      repeatHeaders: true,
      GPSFix: 2,
      GPSPrecision: 500
    });

    const acclData = await goproTelemetry(extractedData, {
      stream: "ACCL",
      repeatSticky: true,
      repeatHeaders: true,
      GPSFix: 2,
      GPSPrecision: 500
    });

    const gyroData = await goproTelemetry(extractedData, {
      stream: "GYRO",
      repeatSticky: true,
      repeatHeaders: true,
      GPSFix: 2,
      GPSPrecision: 500
    });

    const gpsCSV = convertToCSV(gpsData, "GPS5");
    const acclCSV = convertToCSV(acclData, "ACCL");
    const gyroCSV = convertToCSV(gyroData, "GYRO");

    const gpsFilePath = path.join(
      downloadsDir,
      `${videoName}_telemetry_data_GPS5.csv`
    );
    const acclFilePath = path.join(
      downloadsDir,
      `${videoName}_telemetry_data_ACCL.csv`
    );
    const gyroFilePath = path.join(
      downloadsDir,
      `${videoName}_telemetry_data_GYRO.csv`
    );

    await writeFileAsync(gpsFilePath, gpsCSV);
    await writeFileAsync(acclFilePath, acclCSV);
    await writeFileAsync(gyroFilePath, gyroCSV);

    console.log("CSV files generated successfully. Download links:");
    console.log(
      `- GPS5 CSV: http://localhost:5000/downloads/${videoName}_telemetry_data_GPS5.csv`
    );
    console.log(
      `- ACCL CSV: http://localhost:5000/downloads/${videoName}_telemetry_data_ACCL.csv`
    );
    console.log(
      `- GYRO CSV: http://localhost:5000/downloads/${videoName}_telemetry_data_GYRO.csv`
    );

    res.json({
      message: "CSV files generated successfully",
      files: [
        {
          name: `${videoName}_telemetry_data_GPS5.csv`,
          url: `/downloads/${videoName}_telemetry_data_GPS5.csv`
        },
        {
          name: `${videoName}_telemetry_data_ACCL.csv`,
          url: `/downloads/${videoName}_telemetry_data_ACCL.csv`
        },
        {
          name: `${videoName}_telemetry_data_GYRO.csv`,
          url: `/downloads/${videoName}_telemetry_data_GYRO.csv`
        }
      ]
    });

    await writeFileAsync("./out.json", JSON.stringify(extractedData));
    console.log("Telemetry data saved to out.json");

    // Now delete the video file after processing
    fs.unlink(videoPath, (err) => {
      if (err) {
        console.error("Error deleting video file:", err);
      } else {
        console.log(`Successfully deleted video file: ${videoPath}`);
      }
    });
  } catch (error) {
    console.error("Error:", error);
    res.status(500).json({ error: "Failed to extract telemetry data" });
  }
});

function convertToCSV(data, streamName) {
  let csvData = "";

  if (streamName === "GPS5") {
    csvData =
      "cts,date,GPS (Lat.) [deg],GPS (Long.) [deg],GPS (Alt.) [m],GPS (2D speed) [m/s],GPS (3D speed) [m/s],fix,precision\n";
  } else if (streamName === "ACCL") {
    csvData =
      "cts,date,Accelerometer (z) [m/s²],Accelerometer (x) [m/s²],Accelerometer (y) [m/s²],temperature [°C]\n";
  } else if (streamName === "GYRO") {
    csvData =
      "cts,date,Gyroscope (z) [rad/s],Gyroscope (x) [rad/s],Gyroscope (y) [rad/s],temperature [°C]\n";
  }

  for (const deviceId in data) {
    const device = data[deviceId];

    for (const streamName in device.streams) {
      const stream = device.streams[streamName];

      stream.samples.forEach((entry) => {
        const localDate = new Date(entry.date);
        let isoDate = "";

        if (isNaN(localDate)) {
          console.log(`Invalid date: ${entry.date}`);
          isoDate = "Invalid Date";
        } else {
          const utcDate = new Date(
            localDate.getTime() - localDate.getTimezoneOffset() * 60000
          );
          isoDate = utcDate.toISOString();
        }

        if (streamName === "GPS5") {
          csvData += `${entry.cts},${isoDate},${entry["GPS (Lat.) [deg]"]},${entry["GPS (Long.) [deg]"]},${entry["GPS (Alt.) [m]"]},${entry["GPS (2D speed) [m/s]"]},${entry["GPS (3D speed) [m/s]"]},${entry.fix},${entry.precision}\n`;
        } else if (streamName === "ACCL") {
          csvData += `${entry.cts},${isoDate},${entry["Accelerometer (z) [m/s²]"]},${entry["Accelerometer (x) [m/s²]"]},${entry["Accelerometer (y) [m/s²]"]},${entry["temperature [°C]"]}\n`;
        } else if (streamName === "GYRO") {
          csvData += `${entry.cts},${isoDate},${entry["Gyroscope (z) [rad/s]"]},${entry["Gyroscope (x) [rad/s]"]},${entry["Gyroscope (y) [rad/s]"]},${entry["temperature [°C]"]}\n`;
        }
      });
    }
  }

  return csvData;
}

app.use("/downloads", express.static("downloads"));

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
