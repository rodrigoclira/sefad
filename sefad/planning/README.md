# Planning App

## Overview
This Django app manages semester planning and teaching effort calculation based on disciplines offered in a semester.

## Features

### Semester Plans
- Create named plans for different semesters (e.g., "2024.1 Planning")
- Associate plans with specific courses
- Add disciplines individually or by period
- Support for extra classes (multiple turmas of the same discipline)
- Automatic effort calculation

### Effort Calculation
The app automatically calculates:
- **Total Credits**: Sum of all credits considering class count
- **Total CH Relógio**: Sum of all clock hours considering class count
- **Discipline Count**: Number of unique disciplines
- **Classes Count**: Total number of classes (including extra classes)

## Models

### SemesterPlan
Represents a semester planning.

**Fields:**
- `name`: Plan identifier (e.g., "2024.1 Planning")
- `course`: Associated course
- `description`: Additional notes
- `created_at`, `updated_at`: Timestamps

**Methods:**
- `get_total_credits()`: Calculate total credits
- `get_total_ch_relogio()`: Calculate total CH Relógio
- `get_disciplines_count()`: Get total classes count
- `get_unique_disciplines_count()`: Get unique disciplines count

### PlanDiscipline
Represents a discipline within a plan.

**Fields:**
- `plan`: Associated semester plan
- `discipline`: Associated discipline
- `classes_count`: Number of classes (default: 1, allows extra classes)
- `notes`: Additional notes
- `created_at`: Timestamp

**Methods:**
- `get_total_credits()`: Credits × classes_count
- `get_total_ch_relogio()`: CH Relógio × classes_count

## Usage

### Creating a Plan

1. **Via Admin Interface:**
   - Go to `/admin/planning/semesterplan/add/`
   - Enter plan name and select course
   - Add disciplines using the inline form
   - Save to see the effort summary

2. **Adding Disciplines:**
   - **One by one**: Use the inline form in the admin
   - **By period**: Use the management command (see below)
   - **Extra classes**: Set `classes_count` > 1 for disciplines with multiple turmas

### Management Commands

#### Add All Disciplines from a Period

```bash
python manage.py add_period_to_plan <plan_id> <period> [--classes N]
```

**Examples:**
```bash
# Add all period 1 disciplines to plan ID 1
python manage.py add_period_to_plan 1 1

# Add all period 2 disciplines with 2 classes each
python manage.py add_period_to_plan 1 2 --classes 2
```

### Viewing Summaries

The admin interface displays:
- **List view**: Disciplines count, classes count, and effort summary
- **Detail view**: Complete summary with:
  - Unique disciplines
  - Total classes
  - Total credits
  - Total CH Relógio

## Example Workflow

1. **Create a new plan:**
   ```
   Name: "2024.1 - ADS"
   Course: Análise e Desenvolvimento de Sistemas
   ```

2. **Add period 1 disciplines:**
   ```bash
   python manage.py add_period_to_plan 1 1
   ```

3. **Add extra class for a specific discipline:**
   - Edit the PlanDiscipline
   - Change `classes_count` to 2

4. **Add individual disciplines from other periods:**
   - Use the inline form to add specific disciplines

5. **View summary:**
   - Open the plan in admin to see total effort

## Admin Features

- **Inline editing**: Add/edit disciplines directly in the plan form
- **Autocomplete**: Quick search for courses and disciplines
- **Summary display**: Real-time calculation of effort
- **List filters**: Filter by course, period, creation date
- **Search**: Find plans by name or description

## Future Enhancements

- Public-facing views for plan visualization
- Professor assignment to disciplines
- Workload distribution reports
- Comparison between different plans
- Export plans to PDF/Excel
- Conflict detection (same professor, multiple classes)
