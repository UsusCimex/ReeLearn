import React from 'react';
import { Box, Icon } from '@chakra-ui/react';
import { FiSettings } from 'react-icons/fi';

function AdminButton() {
  const handleClick = () => {
    window.location.href = '/admin';
  };

  return (
    <Box
      position="fixed"
      bottom="20px"
      left="20px"
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
        bg="blue.500"
        _hover={{ bg: 'blue.600' }}
        style={{
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)'
        }}
        display="flex"
        alignItems="center"
        justifyContent="center"
        color="white"
      >
        <Icon as={FiSettings} boxSize="24px" />
      </Box>
    </Box>
  );
}

export default AdminButton;
