import React from "react";
import { Typography, Box } from "@mui/material";
import VideoUploadForm from "../components/VideoUploadForm";

const UploadPage = () => (
  <Box>
    <Typography variant="h4" sx={{ mb: 2 }}>Upload Video</Typography>
    <VideoUploadForm />
  </Box>
);

export default UploadPage;
