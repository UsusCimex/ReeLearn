import React from "react";
import { Snackbar, Alert } from "@mui/material";

const AlertMessage = ({ open, onClose, severity, message }) => (
  <Snackbar
    open={open}
    autoHideDuration={5000}
    onClose={onClose}
    anchorOrigin={{ vertical: "top", horizontal: "center" }}
  >
    <Alert onClose={onClose} severity={severity} variant="filled">
      {message}
    </Alert>
  </Snackbar>
);

export default AlertMessage;
