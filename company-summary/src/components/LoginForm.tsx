import { useState } from 'react';
import { validateCredentials } from '../services/auth';
import {
  Paper,
  TextInput,
  PasswordInput,
  Button,
  Text,
  Group,
  Box,
  Alert,
  Stack,
} from '@mantine/core';
import { IconUser, IconLock, IconAlertCircle } from '@tabler/icons-react';

interface LoginFormProps {
  onLogin: (username: string, password: string) => void;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const isValid = await validateCredentials(username, password);
      if (isValid) {
        onLogin(username, password);
      } else {
        setError('Invalid username or password');
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setError('Authentication service unavailable. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box style={{ maxWidth: 480, margin: '0 auto' }}>
      <Paper
        shadow="none"
        p="xl"
        style={{
          background: 'var(--eanna-white)',
          border: '1px solid var(--eanna-gray-200)',
          borderRadius: '0'
        }}
      >
        <Text 
          size="xl" 
          fw={700} 
          ta="center" 
          mb="md"
          style={{ 
            fontFamily: 'var(--eanna-font-serif)',
            color: 'var(--eanna-deep-blue)'
          }}
        >
          Sign In
        </Text>
        <Text 
          size="sm" 
          ta="center" 
          mb="xl"
          style={{ 
            color: 'var(--eanna-gray-600)',
            fontFamily: 'var(--eanna-font-sans)'
          }}
        >
          Access the company analysis dashboard
        </Text>

        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            {error && (
              <Alert icon={<IconAlertCircle size={16} />} color="red" variant="light">
                {error}
              </Alert>
            )}

            <TextInput
              label="Username"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.currentTarget.value)}
              leftSection={<IconUser size={16} />}
              required
              styles={{
                label: { 
                  fontWeight: 500, 
                  color: 'var(--eanna-gray-700)',
                  fontFamily: 'var(--eanna-font-sans)'
                },
                input: {
                  fontFamily: 'var(--eanna-font-sans)',
                  borderColor: 'var(--eanna-gray-300)'
                }
              }}
            />

            <PasswordInput
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              leftSection={<IconLock size={16} />}
              required
              styles={{
                label: { 
                  fontWeight: 500, 
                  color: 'var(--eanna-gray-700)',
                  fontFamily: 'var(--eanna-font-sans)'
                },
                input: {
                  fontFamily: 'var(--eanna-font-sans)',
                  borderColor: 'var(--eanna-gray-300)'
                }
              }}
            />

            <Button
              type="submit"
              fullWidth
              loading={loading}
              size="md"
              mt="md"
              style={{ 
                borderRadius: '0',
                fontWeight: 600,
                backgroundColor: 'var(--eanna-deep-blue)',
                borderColor: 'var(--eanna-deep-blue)',
                fontFamily: 'var(--eanna-font-sans)',
                color: 'var(--eanna-white)'
              }}
            >
              Sign In
            </Button>
          </Stack>
        </form>

        <Group justify="center" mt="xl">
          <Text 
            size="xs" 
            ta="center"
            style={{ 
              color: 'var(--eanna-gray-500)',
              fontFamily: 'var(--eanna-font-sans)'
            }}
          >
            Secure authentication powered by AWS
          </Text>
        </Group>
      </Paper>
    </Box>
  );
}