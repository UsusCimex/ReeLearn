import React from "react";
import UploadVideo from "./components/UploadVideo";
import SearchVideos from "./components/SearchVideos";
import TaskStatus from "./components/TaskStatus";
import VideoFragments from "./components/VideoFragments";

function App() {
  return (
    <div style={{ padding: "20px" }}>
      <h1>ReeLearn</h1>
      <UploadVideo />
      <hr />
      <SearchVideos />
      <hr />
      <TaskStatus />
      <hr />
      <VideoFragments />
    </div>
  );
}

export default App;
