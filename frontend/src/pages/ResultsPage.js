import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Progress,
  IconButton,
} from '@chakra-ui/react';
import { ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import VideoPlayer from '../components/VideoPlayer';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [taskStatus, setTaskStatus] = useState('pending');
  const [results, setResults] = useState([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    const taskId = location.state?.taskId;
    if (!taskId) {
      navigate('/');
      return;
    }

    const checkTaskStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/task/${taskId}`);
        const data = await response.json();

        if (data.status === 'SUCCESS') {
          setTaskStatus('completed');
          setResults(data.result || []);
        } else if (data.status === 'FAILURE') {
          setTaskStatus('failed');
          setError(data.error || 'Task failed');
        } else if (data.status === 'PENDING' || data.status === 'STARTED') {
          setTimeout(checkTaskStatus, 1000);
        }
      } catch (error) {
        setTaskStatus('failed');
        setError('Failed to check task status');
      }
    };

    checkTaskStatus();
  }, [location.state, navigate]);

  const handlePrevVideo = () => {
    setCurrentVideoIndex((prev) => Math.max(0, prev - 1));
  };

  const handleNextVideo = () => {
    setCurrentVideoIndex((prev) => Math.min(results.length - 1, prev + 1));
  };

  if (taskStatus === 'pending') {
    return (
      <Box p={8}>
        <Text mb={4}>Processing your search request...</Text>
        <Progress size="xs" isIndeterminate />
      </Box>
    );
  }

  if (taskStatus === 'failed') {
    return (
      <Box p={8}>
        <Text color="red.500">Error: {error}</Text>
        <Button mt={4} onClick={() => navigate('/')}>Back to Search</Button>
      </Box>
    );
  }

  if (results.length === 0) {
    return (
      <Box p={8}>
        <Text>No results found</Text>
        <Button mt={4} onClick={() => navigate('/')}>Back to Search</Button>
      </Box>
    );
  }

  return (
    <VStack spacing={4} align="stretch" p={4}>
      <Box position="relative">
        <VideoPlayer
          url={results[currentVideoIndex].videoUrl}
          subtitles={results[currentVideoIndex].subtitles}
        />
      </Box>

      <HStack justify="center" spacing={4}>
        <IconButton
          icon={<ChevronLeftIcon />}
          onClick={handlePrevVideo}
          isDisabled={currentVideoIndex === 0}
          aria-label="Previous video"
        />
        <Text>
          Video {currentVideoIndex + 1} of {results.length}
        </Text>
        <IconButton
          icon={<ChevronRightIcon />}
          onClick={handleNextVideo}
          isDisabled={currentVideoIndex === results.length - 1}
          aria-label="Next video"
        />
      </HStack>

      <Button onClick={() => navigate('/')} mt={4}>
        New Search
      </Button>
    </VStack>
  );
}

export default ResultsPage;
