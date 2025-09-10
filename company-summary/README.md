# Company Summary Dashboard

A React + TypeScript application for analyzing company data with secure authentication.

## Getting Started

Install dependencies:

```bash
npm install
```

## Build & Deployment

This project supports three different environments with different authentication configurations:

### Development (Local)
Uses hardcoded credentials for quick local development.

```bash
npm run dev
```

- Authentication: Hardcoded credentials (`admin` / `password123`)
- Available at: `http://localhost:5173`
- Environment file: `.env.development`

### Staging Build
Uses Lambda API authentication (same as production) for testing the full auth flow.

```bash
npm run build:staging
```

- Authentication: AWS Lambda API → Parameter Store
- Deploy `dist/` folder to staging environment
- Environment file: `.env.staging`
- Login: Use actual credentials stored in AWS Parameter Store

### Production Build  
Production-ready build with Lambda API authentication.

```bash
npm run build:prod
```

- Authentication: AWS Lambda API → Parameter Store  
- Deploy `dist/` folder to CloudFront/S3
- Environment file: `.env.production`
- Login: Use actual credentials stored in AWS Parameter Store

## Authentication Architecture

- **Development**: Direct hardcoded credentials in frontend
- **Staging/Production**: Frontend → API Gateway → Lambda → AWS Parameter Store

## Environment Configuration

The app uses different `.env` files for each environment:
- `.env.development` - Local hardcoded credentials
- `.env.staging` - API mode configuration
- `.env.production` - API mode configuration

Authentication credentials for staging/production are stored securely in AWS Systems Manager Parameter Store at:
- `/treville-demo/auth/username`
- `/treville-demo/auth/password`

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
