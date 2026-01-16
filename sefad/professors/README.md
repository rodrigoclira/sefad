# Professors App

## Overview
This Django app manages professor information for the SEFAD system.

## Models

### Professor
Represents a professor in the campus.

**Fields:**
- `name` (CharField): Full name of the professor
- `created_at` (DateTimeField): Timestamp when the record was created
- `updated_at` (DateTimeField): Timestamp when the record was last updated

**Note:** This model is intentionally simple for now and will be expanded with additional fields such as:
- Email
- Department/Area of expertise
- Contact information
- Teaching qualifications
- Available hours
- etc.

## Admin Interface
The Professor model is registered in the Django admin with:
- List display showing name and timestamps
- Search functionality by name
- Collapsible timestamps section
- 50 items per page

## Usage

### Adding Professors
Navigate to `/admin/professors/professor/add/` to add new professors through the admin interface.

### Viewing Professors
Access the professor list at `/admin/professors/professor/` in the admin panel.

## Future Enhancements
- Add more detailed professor information fields
- Create public-facing views to display professor profiles
- Add relationship with disciplines (many-to-many)
- Add workload calculation features
- Add availability scheduling
