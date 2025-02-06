import React from "react";
import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

const Navigation = () => (
  <AppBar position="static">
    <Toolbar>
      <Typography variant="h6" component={RouterLink} to="/" sx={{ flexGrow: 1, textDecoration: "none", color: "inherit" }}>
        ReeLearn
      </Typography>
      <Box>
        <Button color="inherit" component={RouterLink} to="/">
          Home
        </Button>
        <Button color="inherit" component={RouterLink} to="/upload">
          Upload
        </Button>
        <Button color="inherit" component={RouterLink} to="/videos">
          Videos
        </Button>
      </Box>
    </Toolbar>
  </AppBar>
);

export default Navigation;
