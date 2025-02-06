import React, { useState } from "react";
import { Box, TextField, FormControlLabel, Radio, RadioGroup, Button } from "@mui/material";

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState("");
  const [exact, setExact] = useState("false");
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query, exact === "true");
  };
  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
      <TextField
        label="Search"
        variant="outlined"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        fullWidth
      />
      <RadioGroup row value={exact} onChange={(e) => setExact(e.target.value)}>
        <FormControlLabel value="true" control={<Radio />} label="Exact" />
        <FormControlLabel value="false" control={<Radio />} label="Fuzzy" />
      </RadioGroup>
      <Button variant="contained" type="submit">
        Search
      </Button>
    </Box>
  );
};

export default SearchBar;
