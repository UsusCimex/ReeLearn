import React from "react";
import { Box, CircularProgress } from "@mui/material";

const LoadingSpinner = () => (
  <Box
    sx={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: 150,
      py: 4
    }}
  >
    <CircularProgress size={50} />
  </Box>
);

export default LoadingSpinner;
