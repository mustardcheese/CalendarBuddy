# Group Task Assignment Feature

## Overview
Administrators can now create groups and assign tasks to group members. Assigned tasks automatically appear on users' calendars with visual distinction.

## Features Implemented

### 1. Group Management
- **Create Groups**: Any user can create a group and becomes its admin
- **Add Members**: Group admins can add users and assign roles (Admin or Member)
- **Remove Members**: Admins can remove members (except the group creator)
- **View Members**: See all group members and their roles

### 2. Task Assignment
Administrators can assign tasks with the following options:
- **Assign to specific users**: Select individual group members
- **Assign to all members**: Send the task to everyone at once
- **Set deletability**: Mark tasks as required (non-deletable) or optional
- **All standard task fields**: Title, description, date, location, color

### 3. Visual Distinction
Assigned tasks are visually distinct from personal tasks:
- **Dashed border pattern**: Assigned tasks have a distinctive striped background
- **📋 Icon**: Assigned tasks show a clipboard icon
- **🔒 Lock icon**: Non-deletable tasks show a lock icon
- **Task details**: Modal shows who assigned the task and from which group
- **Separate filter view**: Users can view only assigned tasks

### 4. Permission System
- Only group admins can assign tasks
- Tasks can be marked as non-deletable by admins
- Users can see who assigned each task
- Group creators cannot be removed from their groups

## How to Use

### Creating a Group
1. Navigate to "Groups" in the navigation bar
2. Click "Create New Group"
3. Enter group name and optional description
4. You are automatically made an admin of the group

### Adding Members
1. Go to your group's detail page
2. Click "Add Member"
3. Enter the username of the user to add
4. Select their role (Admin or Member)
5. Click "Add Member"

### Assigning Tasks
1. Go to your group's detail page
2. Click "Assign Task"
3. Fill in task details:
   - Title (required)
   - Description (optional)
   - Date (required)
   - Location (optional)
   - Color
4. Choose assignment:
   - Check "Assign to all group members" OR
   - Select specific users from the list
5. Optionally uncheck "Allow users to delete this task" to make it required
6. Click "Assign Task"

### Viewing Assigned Tasks
Users can view their assigned tasks in multiple ways:
- **Calendar View**: Assigned tasks appear with a special striped pattern and 📋 icon
- **My Assigned Tasks**: Navigate to this page from the Groups menu
- **Task Modal**: Click any task to see details including who assigned it

## Database Models

### Group
- `name`: Group name
- `description`: Optional description
- `created_by`: User who created the group
- `created_at`, `updated_at`: Timestamps

### GroupMembership
- `group`: Foreign key to Group
- `user`: Foreign key to User
- `role`: 'admin' or 'member'
- `joined_at`: Timestamp

### Task (Updated)
Added fields:
- `assigned_by`: User who assigned the task (null for personal tasks)
- `group`: Group from which task was assigned (null for personal tasks)
- `is_deletable`: Boolean indicating if user can delete the task

## URLs
- `/groups/` - List all groups
- `/groups/create/` - Create a new group
- `/groups/<id>/` - Group detail page
- `/groups/<id>/add-member/` - Add a member to the group
- `/groups/<id>/assign-task/` - Assign a task to group members
- `/my-assigned-tasks/` - View all tasks assigned to you

## Admin Panel
All models are registered in Django admin for easy management:
- Groups: View and edit all groups
- Group Memberships: Manage user-group relationships
- Tasks: View all tasks including assignment information

## Technical Notes
- Uses Django's built-in User model
- Task model is in the `home` app
- Calendar app now imports Task from home app
- Removed legacy `category` field from tasks
- Full permission checking on delete operations
