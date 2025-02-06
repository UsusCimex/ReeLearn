// src/components/SearchBar.jsx
import React from "react";
import { Box, TextField, FormControl, FormLabel, RadioGroup, FormControlLabel, Radio } from "@mui/material";
import { useTranslation } from "../hooks/useTranslation";

const SearchBar = ({ value, onChange, onSearch, exact, onExactChange }) => {
  const { t } = useTranslation();

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      onSearch(value, exact === "true");
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 2 }}>
      <TextField
        label={t("searchVideos")}
        variant="outlined"
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        fullWidth
      />
      <FormControl component="fieldset">
        <FormLabel component="legend">{t("mode") || "Search Mode"}</FormLabel>
        <RadioGroup row value={exact} onChange={onExactChange}>
          <FormControlLabel value="true" control={<Radio />} label={t("exact")} />
          <FormControlLabel value="false" control={<Radio />} label={t("fuzzy")} />
        </RadioGroup>
      </FormControl>
    </Box>
  );
};

export default SearchBar;
