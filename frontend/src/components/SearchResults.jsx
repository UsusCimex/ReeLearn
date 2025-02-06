import React from "react";
import { Box, Card, CardContent, Typography, Grid } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import VideoPlayer from "./VideoPlayer";
import { useTranslation } from "../hooks/useTranslation";
import { motion } from "framer-motion";

const SearchResults = ({ results, highlightWords, exactSearch }) => {
  const { t } = useTranslation();

  if (!results || results.length === 0) {
    return <Typography>{t("resultNotFound")}</Typography>;
  }

  return (
    <Box sx={{ p: 3 }}>
      {results.map((res) => (
        <motion.div
          key={res.video.video_id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card sx={{ mb: 4 }}>
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
                      fragments={[]} // Режим статичного воспроизведения для фрагмента
                      staticSubtitle={frag.text}
                      searchWords={highlightWords}
                      exactSearch={exactSearch}
                    />
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      {`${t("time")}: ${frag.timecode_start} - ${frag.timecode_end} | Score: ${frag.score}`}
                    </Typography>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </Box>
  );
};

export default SearchResults;
