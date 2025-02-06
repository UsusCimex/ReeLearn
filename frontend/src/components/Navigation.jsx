import React, { useContext } from "react";
import { AppBar, Toolbar, Typography, Button, Box, Select, MenuItem, FormControl, InputLabel } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { LanguageContext } from "../LanguageContext";
import { useTranslation } from "../hooks/useTranslation";

const Navigation = () => {
  const { language, setLanguage } = useContext(LanguageContext);
  const { t } = useTranslation();

  const handleChange = (e) => {
    setLanguage(e.target.value);
  };

  return (
    <AppBar position="static" elevation={4}>
      <Toolbar>
        <Typography variant="h6" component={RouterLink} to="/" sx={{ flexGrow: 1, textDecoration: "none", color: "inherit" }}>
          ReeLearn
        </Typography>
        <Box sx={{ mr: 2 }}>
          <Button color="inherit" component={RouterLink} to="/">
            {t("home")}
          </Button>
          <Button color="inherit" component={RouterLink} to="/upload">
            {t("upload")}
          </Button>
          <Button color="inherit" component={RouterLink} to="/videos">
            {t("videos")}
          </Button>
        </Box>
        <FormControl variant="standard" sx={{ color: "#fff", minWidth: 80 }}>
          <InputLabel sx={{ color: "#fff" }}>{t("language")}</InputLabel>
          <Select
            value={language}
            onChange={handleChange}
            label={t("language")}
            sx={{
              color: "#fff",
              ".MuiSvgIcon-root": { color: "#fff" },
              "&:before": { borderColor: "#fff" },
              "&:after": { borderColor: "#fff" },
            }}
          >
            <MenuItem value="en">EN</MenuItem>
            <MenuItem value="ru">RU</MenuItem>
          </Select>
        </FormControl>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
