import React from "react";
import { Box, Typography, Paper } from "@mui/material";
import VideoUploadForm from "../components/VideoUploadForm";
import { useTranslation } from "../hooks/useTranslation";

const UploadPage = () => {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: { xs: 2, md: 4 } }}>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 2 }}>
          {t("uploadVideo")}
        </Typography>
        <VideoUploadForm />
      </Paper>
    </Box>
  );
};

export default UploadPage;
