import React from "react";
import { Box, Typography, Card, CardContent, Grid } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import VideoPlayer from "../components/VideoPlayer";

const SearchResults = ({ results, highlightWords, exactSearch }) => {
  if (!results || results.length === 0) {
    return <Typography>No results found.</Typography>;
  }

  return (
    <Box sx={{ p: 3 }}>
      {results.map((res) => (
        <Card key={res.video.video_id} sx={{ mb: 4 }}>
          <CardContent>
            <Typography
              variant="h6"
              component={RouterLink}
              to={`/videos/${res.video.video_id}`}
              sx={{ textDecoration: "none", color: "inherit", mb: 1 }}
            >
              {res.video.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {res.video.description}
            </Typography>
            <Grid container spacing={2}>
              {res.fragments.map((frag) => (
                <Grid item xs={12} sm={6} md={4} key={frag.fragment_id}>
                  <VideoPlayer
                    videoUrl={frag.s3_url}
                    fragments={[]} // Статический режим для фрагмента
                    staticSubtitle={frag.text}
                    searchWords={highlightWords}
                    exactSearch={exactSearch}
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {`Time: ${frag.timecode_start} - ${frag.timecode_end} | Score: ${frag.score}`}
                  </Typography>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default SearchResults;
