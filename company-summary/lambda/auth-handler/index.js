const { SSMClient, GetParameterCommand } = require('@aws-sdk/client-ssm');

const ssmClient = new SSMClient({ 
  region: process.env.AWS_REGION || 'us-east-1'
});

exports.handler = async (event) => {
  console.log('Lambda function started');
  console.log('Event received:', JSON.stringify(event, null, 2));

  // With non-proxy integration, the event IS the request body
  const { username, password } = event;

  console.log('Received credentials for authentication');

  if (!username || !password) {
    console.log('Missing username or password');
    return {
      error: 'Username and password are required'
    };
  }

  try {
    console.log('Fetching credentials from Parameter Store...');

    // Fetch stored credentials from Parameter Store
    const [usernameResponse, passwordResponse] = await Promise.all([
      ssmClient.send(new GetParameterCommand({
        Name: '/treville-demo/auth/username',
        WithDecryption: false
      })),
      ssmClient.send(new GetParameterCommand({
        Name: '/treville-demo/auth/password',
        WithDecryption: true
      }))
    ]);

    const storedUsername = usernameResponse.Parameter?.Value;
    const storedPassword = passwordResponse.Parameter?.Value;

    console.log('Successfully retrieved credentials from Parameter Store');

    if (!storedUsername || !storedPassword) {
      console.log('Missing stored credentials in Parameter Store');
      return {
        error: 'Authentication configuration not found'
      };
    }

    // Validate credentials
    const isValid = storedUsername === username && storedPassword === password;
    console.log('Credential validation result:', isValid);

    const response = {
      valid: isValid,
      message: isValid ? 'Authentication successful' : 'Invalid credentials'
    };

    console.log('Returning response:', response);
    return response;

  } catch (error) {
    console.error('Authentication error:', error);
    console.error('Error stack:', error.stack);
    
    const errorResponse = {
      error: 'Internal server error',
      message: 'Authentication service temporarily unavailable'
    };

    console.log('Returning error response:', errorResponse);
    return errorResponse;
  }
};