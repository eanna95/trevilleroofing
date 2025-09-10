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
      background: 'transparent',
      padding: '0',
      position: 'relative'
    }}>
      
      {/* Enhanced Dynamic Header */}
      <div className="executive-header" style={{
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.98) 50%, rgba(240, 249, 255, 0.95) 100%)',
        padding: '1.2rem 0',
        borderBottom: '3px solid rgba(59, 130, 246, 0.4)',
        boxShadow: '0 8px 32px rgba(29, 78, 216, 0.12), 0 4px 16px rgba(59, 130, 246, 0.08)',
        position: 'relative',
        overflow: 'hidden',
        backdropFilter: 'blur(12px) saturate(120%)'
      }}>
        
        <Container size="xl" style={{ maxWidth: '1600px', position: 'relative', zIndex: 1 }}>
          <Group justify="space-between" align="center">
            <Group align="center" gap="lg">
              {/* Transparent Logo Container */}
              <div className="logo-container" style={{
                background: 'transparent',
                padding: '8px 16px',
                borderRadius: '8px',
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.3s cubic-bezier(0.23, 1, 0.32, 1)'
              }}>
                
                <img 
                  src="/treville-logo.svg" 
                  alt="Treville Roofing" 
                  style={{
                    height: '45px',
                    width: 'auto',
                    display: 'block',
                    filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.1))',
                    position: 'relative',
                    zIndex: 1,
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'scale(1.05)';
                    e.currentTarget.style.filter = 'drop-shadow(0 2px 8px rgba(0,81,163,0.3))';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.filter = 'drop-shadow(0 1px 2px rgba(0,0,0,0.1))';
                  }}
                />
              </div>
              
              <div style={{ borderLeft: '1px solid var(--mc-primary-200)', height: '40px', margin: '0 8px' }} />
              
              <div>
                <Title 
                  order={1} 
                  size="1.75rem"
                  fw={300}
                  style={{ 
                    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
                    color: 'var(--mc-midnight)',
                    letterSpacing: '-0.01em',
                    lineHeight: '1.2',
                    margin: 0
                  }}
                >
                  ROOFING COMPANY ANALYSIS
                </Title>
                <p style={{
                  color: 'var(--mc-primary-500)',
                  fontSize: '0.85rem',
                  fontWeight: 400,
                  letterSpacing: '0.08em',
                  marginTop: '2px',
                  fontFamily: "'Inter', sans-serif",
                  textTransform: 'uppercase'
                }}>
                  Executive Dashboard
                </p>
              </div>
            </Group>
            
            {isAuthenticated && (
              <Button 
                variant="outline" 
                leftSection={<IconLogout size={18} />}
                onClick={onLogout}
                className="signout-button-light"
                style={{
                  fontSize: '0.95rem',
                  letterSpacing: '0.05em',
                  color: 'var(--mc-midnight)',
                  borderColor: 'var(--mc-primary-300)'
                }}
              >
                Sign Out
              </Button>
            )}
          </Group>
        </Container>
      </div>

      {/* Content Section with Dynamic Visual Impact */}
      <Container size="xl" style={{ paddingTop: '1rem', paddingBottom: '1rem', maxWidth: '100%' }}>
        <Paper 
          shadow="xl" 
          p="xl"
          style={{
            background: 'white',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '12px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            overflow: 'hidden',
            position: 'relative'
          }}
        >
          {isAuthenticated ? <CompanyTable /> : <LoginForm onLogin={onLogin} />}
        </Paper>
      </Container>
    </div>
  );
}