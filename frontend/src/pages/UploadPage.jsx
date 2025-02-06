// src/pages/UploadPage.jsx
import React from "react";
import { Box, Typography, Paper } from "@mui/material";
import VideoUploadForm from "../components/VideoUploadForm";
import { useTranslation } from "../hooks/useTranslation";

const UploadPage = () => {
  const { t } = useTranslation();
  return (
    <Box
      sx={{
        p: { xs: 2, md: 4 },
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "80vh",
        background: "linear-gradient(135deg, #f5f7fa, #c3cfe2)"
      }}
    >
      <Paper
        sx={{
          p: 4,
          width: { xs: "100%", md: "60%" },
          maxWidth: 600,
          borderRadius: 3,
          boxShadow: 3
        }}
      >
        <Typography
          variant="h4"
          sx={{ mb: 3, textAlign: "center", fontWeight: "bold" }}
        >
          {t("uploadVideo")}
        </Typography>
        <VideoUploadForm />
      </Paper>
    </Box>
  );
};

export default UploadPage;
