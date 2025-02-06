import React from "react";
import { Typography, Box } from "@mui/material";
import VideoUploadForm from "../components/VideoUploadForm";
import { useTranslation } from "../hooks/useTranslation";

const UploadPage = () => {
  const { t } = useTranslation();

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>{t("uploadVideo")}</Typography>
      <VideoUploadForm />
    </Box>
  );
};

export default UploadPage;
