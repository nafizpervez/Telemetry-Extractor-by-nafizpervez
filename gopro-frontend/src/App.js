import React, { useState, useRef } from "react";
import axios from "axios";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faRefresh,
  faCheckCircle,
  faCopyright
} from "@fortawesome/free-solid-svg-icons";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloadLinks, setDownloadLinks] = useState(null);
  const [progress, setProgress] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [uploadAbort, setUploadAbort] = useState(false);
  const abortControllerRef = useRef(new AbortController());

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setCompleted(false);
    setDownloadLinks(null);
    setProgress(0);
    setUploadAbort(false);
  };

  const handleFileUpload = async () => {
    if (!file) {
      alert("Please select a file to upload");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("video", file);

    try {
      const response = await axios.post(
        // "http://172.16.1.16:5000/upload",
        "http://localhost:5000/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data"
          },
          onUploadProgress: (progressEvent) => {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setProgress(percent);
          },
          signal: abortControllerRef.current.signal
        }
      );

      setDownloadLinks(response.data.files);
      setCompleted(true);
      setLoading(false);
    } catch (error) {
      if (axios.isCancel(error)) {
        console.log("Upload aborted");
      } else {
        console.error("Error uploading file:", error);
        alert("There was an error uploading the file. Please try again.");
      }
      setLoading(false);
    }
  };

  const downloadCSV = (url, filename) => {
    axios
      .get(`http://172.16.1.16:5000${url}`, { responseType: "blob" })
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
      })
      .catch((error) => {
        console.error("Error downloading the file", error);
        alert("There was an error downloading the file. Please try again.");
      });
  };

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="App">
      <h1 className="header-text">TELEMETRY EXTRACTOR</h1>
      <p className="sub-header">for GoPro</p>
      <input
        type="file"
        onChange={handleFileChange}
        accept="video/mp4,video/x-m4v,video/*"
      />
      <button onClick={handleFileUpload} disabled={loading || uploadAbort}>
        {loading ? "Uploading..." : "Upload and Extract Telemetry"}
      </button>

      {loading && (
        <div className="progress-container">
          <progress value={progress} max="100" />
          <p>{progress}%</p>
        </div>
      )}

      {completed && !loading && !uploadAbort && (
        <div style={{ marginTop: "20px", animation: "fadeIn 1s" }}>
          <div className="checkmark">
            <FontAwesomeIcon
              icon={faCheckCircle}
              size="3x"
              className="checkmark-icon"
            />
          </div>
          <p>Extraction Completed</p>
        </div>
      )}

      {downloadLinks && !loading && !uploadAbort && (
        <div style={{ marginTop: "20px" }}>
          <button
            onClick={() =>
              downloadCSV(downloadLinks[0].url, downloadLinks[0].name)
            }
          >
            Download GPS5 CSV
          </button>
          <button
            onClick={() =>
              downloadCSV(downloadLinks[1].url, downloadLinks[1].name)
            }
          >
            Download ACCL CSV
          </button>
          <button
            onClick={() =>
              downloadCSV(downloadLinks[2].url, downloadLinks[2].name)
            }
          >
            Download GYRO CSV
          </button>
        </div>
      )}

      {/* General Buttons always visible */}
      <div style={{ marginTop: "20px" }}>
        <button className="reload-halt-button" onClick={handleReload}>
          <FontAwesomeIcon icon={faRefresh} /> Reload
        </button>
      </div>
      <footer className="footer">
        <p>
          All Rights Reserved <FontAwesomeIcon icon={faCopyright} />{" "}
          <a
            href="https://esribangladesh.com.bd/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Esri Bangladesh
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
