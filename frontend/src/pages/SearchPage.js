import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  VStack,
  Input,
  Button,
  FormControl,
  FormLabel,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  useToast
} from '@chakra-ui/react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function SearchPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [query, setQuery] = useState('');
  const [params, setParams] = useState({
    threshold: 0.5,
    maxResults: 5
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a search query',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsLoading(true);
    try {
      const queryParams = new URLSearchParams({
        query,
        ...params
      });
      const response = await fetch(`${API_BASE_URL}/search?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const data = await response.json();
      if (data.task_id) {
        navigate('/results', { state: { taskId: data.task_id } });
      } else {
        throw new Error('No task ID received');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to start search. Please try again.',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box maxW="600px" mx="auto" mt={10}>
      <VStack spacing={6} align="stretch">
        <FormControl>
          <FormLabel>Search Query</FormLabel>
          <Input
            size="lg"
            placeholder="Enter your search query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Similarity Threshold: {params.threshold}</FormLabel>
          <Slider
            value={params.threshold}
            min={0}
            max={1}
            step={0.1}
            onChange={(value) => setParams({ ...params, threshold: value })}
          >
            <SliderTrack>
              <SliderFilledTrack />
            </SliderTrack>
            <SliderThumb />
          </Slider>
        </FormControl>

        <FormControl>
          <FormLabel>Max Results: {params.maxResults}</FormLabel>
          <Slider
            value={params.maxResults}
            min={1}
            max={10}
            step={1}
            onChange={(value) => setParams({ ...params, maxResults: value })}
          >
            <SliderTrack>
              <SliderFilledTrack />
            </SliderTrack>
            <SliderThumb />
          </Slider>
        </FormControl>

        <Button
          colorScheme="blue"
          size="lg"
          onClick={handleSearch}
          isLoading={isLoading}
        >
          Search
        </Button>
      </VStack>
    </Box>
  );
}

export default SearchPage;
