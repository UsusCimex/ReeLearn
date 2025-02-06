// src/components/Navigation.jsx
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
    <AppBar
      position="sticky"
      elevation={6}
      sx={{
        background: "linear-gradient(45deg, #0d47a1, #1976d2)",
        paddingX: 2
      }}
    >
      <Toolbar sx={{ justifyContent: "space-between", gap: 2 }}>
        {/* Логотип */}
        <Typography
          variant="h5"
          component={RouterLink}
          to="/"
          sx={{
            textDecoration: "none",
            color: "#fff",
            fontWeight: "bold",
            transition: "transform 0.3s",
            "&:hover": { transform: "scale(1.05)" }
          }}
        >
          ReeLearn
        </Typography>

        {/* Навигационные ссылки */}
        <Box sx={{ display: "flex", alignItems: "center", gap: { xs: 1, sm: 2 } }}>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
            sx={{
              textTransform: "none",
              fontSize: { xs: "0.9rem", sm: "1rem" },
              transition: "color 0.3s, transform 0.3s",
              "&:hover": { color: "#ffeb3b", transform: "scale(1.05)" }
            }}
          >
            {t("home")}
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/upload"
            sx={{
              textTransform: "none",
              fontSize: { xs: "0.9rem", sm: "1rem" },
              transition: "color 0.3s, transform 0.3s",
              "&:hover": { color: "#ffeb3b", transform: "scale(1.05)" }
            }}
          >
            {t("upload")}
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/videos"
            sx={{
              textTransform: "none",
              fontSize: { xs: "0.9rem", sm: "1rem" },
              transition: "color 0.3s, transform 0.3s",
              "&:hover": { color: "#ffeb3b", transform: "scale(1.05)" }
            }}
          >
            {t("videos")}
          </Button>
        </Box>

        {/* Селектор языка */}
        <FormControl variant="standard" sx={{ minWidth: 80 }}>
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
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
