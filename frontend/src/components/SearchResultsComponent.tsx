import React, { useState } from 'react';
import { searchResult, searchStatus } from '../types/index';
import { Box, Typography, IconButton } from '@mui/material';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

interface SearchResultsProps {
    search_status: searchStatus;
    search_results?: searchResult[];
    on_video_select: (video_id: string) => void;
}

const SearchResultsComponent: React.FC<SearchResultsProps> = ({ search_status, search_results, on_video_select }) => {
    const [expanded_videos, setExpandedVideos] = useState<Set<string>>(new Set());

    const toggle_video = (video_id: string) => {
        const new_expanded_videos = new Set(expanded_videos);
        if (expanded_videos.has(video_id)) {
            new_expanded_videos.delete(video_id);
        } else {
            new_expanded_videos.add(video_id);
        }
        setExpandedVideos(new_expanded_videos);
    };

    if (!search_results || search_results.length === 0) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography>No results found</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            {search_results.map((result) => (
                <Box key={result.video_id} sx={{ mb: 2 }}>
                    <Box 
                        sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            cursor: 'pointer' 
                        }}
                        onClick={() => toggle_video(result.video_id)}
                    >
                        <IconButton size="small">
                            {expanded_videos.has(result.video_id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                        <Typography variant="h6" sx={{ ml: 1 }}>
                            {result.name} ({result.fragments_count} fragments)
                        </Typography>
                    </Box>
                    {expanded_videos.has(result.video_id) && (
                        <Box sx={{ ml: 4, mt: 1 }}>
                            <Typography 
                                sx={{ cursor: 'pointer', color: 'primary.main' }}
                                onClick={() => on_video_select(result.video_id)}
                            >
                                View Video
                            </Typography>
                        </Box>
                    )}
                </Box>
            ))}
        </Box>
    );
};

export default SearchResultsComponent;
