# Wolt Discounts App

A mobile web application that displays stores with discounts from Wolt. The app is built with React for the frontend and Flask for the backend API.

## Features

- View all stores that have discounted items
- Browse discounted products for each store
- Open products directly in the Wolt app
- Support for English and Russian languages
- Responsive mobile-first design with 2025 minimalist style

## Prerequisites

- Node.js (v14 or higher)
- Python (v3.7 or higher)
- SQLite database with Wolt discounts data

## Installation

### Backend

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Make sure the `wolt_discounts.db` file is in the correct location

### Frontend

1. Install Node.js dependencies:
   ```
   npm install
   ```

## Running the Application

1. Start the Flask backend server:
   ```
   python server.py
   ```

2. In a separate terminal, start the React development server:
   ```
   npm start
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

## Building for Production

To create a production build:

```
npm run build
```

The build files will be created in the `build` directory, which can be served by the Flask backend.
