import React from "react";
import { Alert, Snackbar } from "@mui/material";

const AlertMessage = ({ open, onClose, severity, message }) => {
  return (
    <Snackbar open={open} autoHideDuration={5000} onClose={onClose} anchorOrigin={{ vertical: "top", horizontal: "center" }}>
      <Alert onClose={onClose} severity={severity} variant="filled">
        {message}
      </Alert>
    </Snackbar>
  );
};

export default AlertMessage;
