import React, { useState } from "react";
import { Box, VStack, Input, Button, Heading, Divider, Text, Container, useToast, FormControl, FormLabel } from "@chakra-ui/react";
import { FiHome } from "react-icons/fi";

const API_BASE_URL = 'http://localhost:8000/api/v1';

function UploadVideo() {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const toast = useToast();

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    // Set default name from file name if not already set
    if (!name && event.target.files[0]) {
      setName(event.target.files[0].name);
    }
  };

  const handleUpload = async () => {
    if (!file || !name.trim()) return;

    const formData = new FormData();
    formData.append('video_file', file);
    formData.append('name', name);
    if (description.trim()) {
      formData.append('description', description);
    }

    setUploading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      
      const data = await response.json();
      toast({
        title: "Upload Success",
        description: `Task ID: ${data.task_id}`,
        status: "success",
        duration: 5000,
      });
      
      // Reset form
      setFile(null);
      setName('');
      setDescription('');
    } catch (error) {
      toast({
        title: "Upload Failed",
        description: error.message,
        status: "error",
        duration: 5000,
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <Heading size="md">Upload Video</Heading>
      <FormControl isRequired>
        <FormLabel>Video File</FormLabel>
        <Input
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          disabled={uploading}
          p={1}
        />
      </FormControl>
      
      <FormControl isRequired>
        <FormLabel>Name</FormLabel>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter video name"
          disabled={uploading}
        />
      </FormControl>
      
      <FormControl>
        <FormLabel>Description (optional)</FormLabel>
        <Input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter video description"
          disabled={uploading}
        />
      </FormControl>
      
      <Button
        colorScheme="blue"
        onClick={handleUpload}
        isLoading={uploading}
        isDisabled={!file || !name.trim() || uploading}
      >
        {uploading ? 'Uploading...' : 'Upload'}
      </Button>
    </VStack>
  );
}

function SearchVideos() {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const toast = useToast();

  const handleSearch = async () => {
    if (!query.trim()) return;

    setSearching(true);
    try {
      const queryParams = new URLSearchParams({ query });
      const response = await fetch(`${API_BASE_URL}/search?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      const data = await response.json();
      toast({
        title: "Search Started",
        description: `Task ID: ${data.task_id}`,
        status: "success",
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: "Search Failed",
        description: error.message,
        status: "error",
        duration: 5000,
      });
    } finally {
      setSearching(false);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <Heading size="md">Search Videos</Heading>
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter search query"
      />
      <Button
        colorScheme="blue"
        onClick={handleSearch}
        isLoading={searching}
      >
        {searching ? 'Searching...' : 'Search'}
      </Button>
    </VStack>
  );
}

function TaskStatus() {
  const [taskId, setTaskId] = useState('');
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [polling, setPolling] = useState(false);

  const fetchStatus = async () => {
    if (!taskId.trim()) return;

    try {
      const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`);
      if (!response.ok) {
        throw new Error(response.status === 404 ? "Task not found" : "Failed to fetch status");
      }
      const data = await response.json();
      setStatus(data);
      setError(null);

      // Continue polling if task is not in a final state
      if (data.status === 'pending' || data.status === 'processing') {
        return true;
      }
      return false;
    } catch (error) {
      setError(error.message);
      setStatus(null);
      return false;
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <Heading size="md">Check Task Status</Heading>
      <Input
        value={taskId}
        onChange={(e) => setTaskId(e.target.value)}
        placeholder="Enter task ID"
      />
      <Button colorScheme="blue" onClick={fetchStatus}>
        Check Status
      </Button>
      {status && (
        <Box
          p={4}
          bg="gray.50"
          borderRadius="md"
          fontFamily="monospace"
          whiteSpace="pre-wrap"
        >
          {JSON.stringify(status, null, 2)}
        </Box>
      )}
      {error && (
        <Box
          p={4}
          bg="red.50"
          borderRadius="md"
          fontFamily="monospace"
          whiteSpace="pre-wrap"
        >
          {error}
        </Box>
      )}
    </VStack>
  );
}

function VideoFragments() {
  const [videoId, setVideoId] = useState('');
  const [fragments, setFragments] = useState([]);
  const toast = useToast();

  const fetchFragments = async () => {
    if (!videoId.trim()) {
      toast({
        title: "Error",
        description: "Please enter a video ID",
        status: "error",
        duration: 3000,
      });
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/videos/${videoId}/fragments`);
      if (!response.ok) {
        throw new Error(response.status === 404 ? "Video not found" : "Failed to fetch fragments");
      }
      const data = await response.json();
      setFragments(data.fragments || []);
      
      if (data.fragments.length === 0) {
        toast({
          title: "No Fragments",
          description: "No fragments found for this video",
          status: "info",
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        status: "error",
        duration: 3000,
      });
      setFragments([]);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <Heading size="md">Video Fragments</Heading>
      <FormControl>
        <FormLabel>Video ID</FormLabel>
        <Input
          value={videoId}
          onChange={(e) => setVideoId(e.target.value)}
          placeholder="Enter video ID"
          type="number"
        />
      </FormControl>
      <Button 
        colorScheme="blue" 
        onClick={fetchFragments}
        isDisabled={!videoId.trim()}
      >
        Get Fragments
      </Button>
      
      {fragments.length > 0 && (
        <VStack spacing={6} align="stretch">
          {fragments.map((fragment) => (
            <Box 
              key={fragment.id} 
              p={4} 
              bg="white" 
              borderRadius="md" 
              boxShadow="sm"
              border="1px"
              borderColor="gray.200"
            >
              <Heading size="sm" mb={2}>Fragment {fragment.id}</Heading>
              {fragment.s3_url && (
                <video
                  controls
                  width="100%"
                  style={{ borderRadius: '0.375rem', marginBottom: '0.5rem' }}
                >
                  <source src={fragment.s3_url} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              )}
              <Text><strong>Start Time:</strong> {fragment.timecode_start.toFixed(2)}s</Text>
              <Text><strong>End Time:</strong> {fragment.timecode_end.toFixed(2)}s</Text>
              {fragment.text && (
                <Text mt={2}>
                  <strong>Text:</strong> {fragment.text}
                </Text>
              )}
              {fragment.tags && fragment.tags.length > 0 && (
                <Text mt={2}>
                  <strong>Tags:</strong> {fragment.tags.join(', ')}
                </Text>
              )}
            </Box>
          ))}
        </VStack>
      )}
    </VStack>
  );
}

// Create a return button component similar to AdminButton
function ReturnButton() {
  const handleClick = () => {
    window.location.href = '/';
  };

  return (
    <Box
      position="fixed"
      bottom="20px"
      right="20px"
      onClick={handleClick}
      cursor="pointer"
      transition="transform 0.2s"
      _hover={{ transform: 'scale(1.1)' }}
    >
      <Box
        as="button"
        width="50px"
        height="50px"
        position="relative"
        bg="green.500"
        _hover={{ bg: 'green.600' }}
        style={{
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)'
        }}
        display="flex"
        alignItems="center"
        justifyContent="center"
        color="white"
      >
        <FiHome size="24px" />
      </Box>
    </Box>
  );
}

function OldInterface() {
  return (
    <Box bg="gray.100" minH="100vh" py={8}>
      <Container maxW="container.md" bg="white" p={8} borderRadius="lg" boxShadow="md">
        <VStack spacing={8} align="stretch">
          <Heading>ReeLearn Admin Interface</Heading>
          <UploadVideo />
          <Divider />
          <SearchVideos />
          <Divider />
          <TaskStatus />
          <Divider />
          <VideoFragments />
        </VStack>
      </Container>
      <ReturnButton />
    </Box>
  );
}

export default OldInterface;
