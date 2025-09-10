import { Container, Title, Paper, Group, Button } from '@mantine/core';
import { IconLogout } from '@tabler/icons-react';
import { CompanyTable } from '../components/CompanyTable';
import { LoginForm } from '../components/LoginForm';

interface SummaryProps {
  isAuthenticated: boolean;
  onLogin: (username: string, password: string) => void;
  onLogout: () => void;
}

export function Summary({ isAuthenticated, onLogin, onLogout }: SummaryProps) {
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, var(--eanna-gray-100) 0%, var(--eanna-light-blue) 100%)',
      padding: '0'
    }}>
      
      {/* Professional Header with Gradient */}
      <div style={{
        background: 'linear-gradient(135deg, var(--eanna-deep-blue) 0%, var(--eanna-electric-blue) 50%, var(--eanna-cyan) 100%)',
        padding: '3rem 0',
        borderBottom: '4px solid var(--eanna-accent-gold)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.15)'
      }}>
        <Container size="xl" style={{ maxWidth: '1400px' }}>
          <Group justify="space-between" align="center">
            <div>
              <Title 
                order={1} 
                size="3.2rem"
                fw={800}
                mb="xs"
                style={{ 
                  fontFamily: "'Cormorant Garamond', 'Crimson Text', Georgia, serif",
                  fontWeight: 800,
                  color: 'var(--eanna-white)',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  letterSpacing: '1px',
                  lineHeight: '1.1'
                }}
              >
                Treville Roofing Company Analysis
              </Title>
              <div style={{
                height: '3px',
                width: '120px',
                background: 'var(--eanna-accent-gold)',
                marginTop: '1rem',
                borderRadius: '2px'
              }} />
            </div>
            {isAuthenticated && (
              <Button 
                variant="outline" 
                leftSection={<IconLogout size={18} />}
                onClick={onLogout}
                className="signout-button"
              >
                Sign Out
              </Button>
            )}
          </Group>
        </Container>
      </div>

      {/* Content Section with Professional Styling */}
      <Container size="xl" style={{ paddingTop: '4rem', paddingBottom: '2rem', maxWidth: '1400px' }}>
        <Paper 
          shadow="xl" 
          p="xl"
          style={{
            background: 'var(--eanna-white)',
            border: '1px solid var(--eanna-gray-300)',
            borderRadius: '12px',
            boxShadow: '0 16px 64px rgba(0,0,0,0.12)',
            overflow: 'hidden'
          }}
        >
          {isAuthenticated ? <CompanyTable /> : <LoginForm onLogin={onLogin} />}
        </Paper>
      </Container>
    </div>
  );
}