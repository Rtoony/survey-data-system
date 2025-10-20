# ACAD-GIS Schema Explorer & Data Manager

A companion tool for viewing and managing your ACAD-GIS Supabase database.

## Features

- **Schema Viewer** - Browse all tables, columns, data types, and row counts
- **Projects Manager** - View and delete projects with drawing counts
- **Drawings Manager** - Browse and delete drawings with filtering
- **Real-time Updates** - Connects directly to Supabase, auto-reflects changes
- **Mission Control Theme** - Matches your ACAD-GIS aesthetic

## Setup

1. **Install Dependencies** (already done via Replit)
   ```bash
   pip install flask psycopg2-binary python-dotenv flask-cors
   ```

2. **Configure Database Connection**
   
   Create a `.env` file with your Supabase credentials:
   ```
   DB_HOST=your-project.supabase.co
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=your-password-here
   ```

3. **Run the App**
   ```bash
   python app.py
   ```

4. **Access the Tool**
   
   Open your browser to `http://localhost:5000`

## Usage

### Schema Viewer
- View all database tables
- See column definitions and data types
- Check row counts for each table
- Perfect for understanding your database structure

### Projects Manager
- Browse all projects with drawing counts
- Delete test projects easily
- See creation dates and client info
- Cascading deletes (deletes associated drawings)

### Drawings Manager
- View all drawings across projects
- Filter by project name
- Delete individual drawings
- See which drawings have DXF content

## Architecture

This tool:
- Connects directly to your Supabase PostgreSQL database
- Uses Flask backend with simple REST API
- Frontend uses your Mission Control theme
- Auto-updates whenever database changes

## Why This Tool?

While your main ACAD-GIS tool is for production work, this Schema Explorer is perfect for:
- Quick database inspection during development
- Cleaning up test data
- Understanding table relationships
- Verifying schema changes
- Prototyping UI patterns

## Safety

This tool provides:
- Read access to all data (schema viewer)
- Delete operations (with confirmation dialogs)
- No create/update operations (use your main tool for that)

Always verify before deleting production data!
