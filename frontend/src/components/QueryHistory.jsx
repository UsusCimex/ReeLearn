// src/components/QueryHistory.jsx
import React from "react";
import { List, ListItem, ListItemButton, ListItemText, Paper, Typography } from "@mui/material";
import { useTranslation } from "../hooks/useTranslation";

const QueryHistory = ({ history, onSelect }) => {
  const { t } = useTranslation();

  if (!history || history.length === 0) return null;

  return (
    <Paper sx={{ mt: 1, mb: 2, p: 1 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>
        {t("recentSearches")}
      </Typography>
      <List>
        {history.map((q, index) => (
          <ListItem key={index} disablePadding>
            <ListItemButton onClick={() => onSelect(q)}>
              <ListItemText primary={q} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default QueryHistory;
