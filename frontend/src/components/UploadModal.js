import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  Progress,
  Text,
  useToast,
  Input,
} from '@chakra-ui/react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function UploadModal({ isOpen, onClose }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const toast = useToast();

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === 'video/mp4') {
      setFile(selectedFile);
    } else {
      toast({
        title: 'Invalid file type',
        description: 'Please select an MP4 video file',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('video', file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.task_id) {
        // Start polling for task status
        const checkStatus = async () => {
          const statusResponse = await fetch(`${API_BASE_URL}/task/${data.task_id}`);
          const statusData = await statusResponse.json();

          if (statusData.status === 'SUCCESS') {
            toast({
              title: 'Upload complete',
              description: 'Video has been processed successfully',
              status: 'success',
              duration: 5000,
            });
            onClose();
          } else if (statusData.status === 'FAILURE') {
            throw new Error(statusData.error || 'Upload failed');
          } else {
            // Update progress based on task status
            setProgress((prev) => Math.min(prev + 10, 90));
            setTimeout(checkStatus, 1000);
          }
        };

        checkStatus();
      } else {
        throw new Error('No task ID received');
      }
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: error.message || 'Please try again',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setUploading(false);
      setProgress(0);
      setFile(null);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Upload Video</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <Input
              type="file"
              accept="video/mp4"
              onChange={handleFileChange}
              disabled={uploading}
            />
            {uploading && (
              <>
                <Progress
                  value={progress}
                  size="xs"
                  width="100%"
                  colorScheme="blue"
                />
                <Text>Processing video... {progress}%</Text>
              </>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button
            colorScheme="blue"
            mr={3}
            onClick={handleUpload}
            isLoading={uploading}
            disabled={!file || uploading}
          >
            Upload
          </Button>
          <Button variant="ghost" onClick={onClose} disabled={uploading}>
            Cancel
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

export default UploadModal;
