import React from "react";
import { List, ListItem, ListItemText, Typography } from "@mui/material";

const FragmentList = ({ fragments }) => {
  if (!fragments || fragments.length === 0) {
    return <Typography>No fragments available.</Typography>;
  }
  return (
    <List>
      {fragments.map((frag) => (
        <ListItem key={frag.id}>
          <ListItemText primary={frag.text} secondary={`[${frag.timecode_start} - ${frag.timecode_end}]`} />
        </ListItem>
      ))}
    </List>
  );
};

export default FragmentList;
