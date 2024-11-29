import React from 'react';
import { Box, Button, Flex, Heading, useDisclosure } from '@chakra-ui/react';
import UploadModal from './UploadModal';

function Header() {
  const { isOpen, onOpen, onClose } = useDisclosure();

  return (
    <Box bg="white" shadow="sm" py={4}>
      <Flex maxW="container.xl" mx="auto" px={4} justify="space-between" align="center">
        <Heading size="lg" color="blue.600">ReeLearn</Heading>
        <Button colorScheme="blue" onClick={onOpen}>Upload Video</Button>
      </Flex>
      <UploadModal isOpen={isOpen} onClose={onClose} />
    </Box>
  );
}

export default Header;
