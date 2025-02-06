import React from "react";
import { CircularProgress, Box } from "@mui/material";

const LoadingSpinner = () => (
  <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 150 }}>
    <CircularProgress />
  </Box>
);

export default LoadingSpinner;
