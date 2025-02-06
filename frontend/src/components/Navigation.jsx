import React, { useContext } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from "@mui/material";
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
    <AppBar position="sticky" elevation={4}>
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Typography
          variant="h5"
          component={RouterLink}
          to="/"
          sx={{
            textDecoration: "none",
            color: "inherit",
            fontWeight: "bold"
          }}
        >
          ReeLearn
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Button color="inherit" component={RouterLink} to="/">
            {t("home")}
          </Button>
          <Button color="inherit" component={RouterLink} to="/upload">
            {t("upload")}
          </Button>
          <Button color="inherit" component={RouterLink} to="/videos">
            {t("videos")}
          </Button>
          <FormControl variant="standard" sx={{ minWidth: 80, color: "#fff" }}>
            <InputLabel sx={{ color: "#fff" }}>{t("language")}</InputLabel>
            <Select
              value={language}
              onChange={handleChange}
              label={t("language")}
              sx={{
                color: "#fff",
                ".MuiSvgIcon-root": { color: "#fff" },
                "&:before": { borderColor: "#fff" },
                "&:after": { borderColor: "#fff" }
              }}
            >
              <MenuItem value="en">EN</MenuItem>
              <MenuItem value="ru">RU</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
