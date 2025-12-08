from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Project, ProjectMembership, Task, Group, GroupMembership
from datetime import date


class ProjectModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='admin_user', password='testpass123')
        self.user2 = User.objects.create_user(username='collab_user', password='testpass123')
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            created_by=self.user1
        )

    def test_project_creation(self):
        """Test that a project can be created"""
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.created_by, self.user1)

    def test_project_str(self):
        """Test project string representation"""
        self.assertEqual(str(self.project), 'Test Project')

    def test_project_membership_creation(self):
        """Test that memberships can be created"""
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.user1,
            role='admin'
        )
        self.assertEqual(membership.role, 'admin')
        self.assertTrue(membership.is_admin())

    def test_project_is_admin(self):
        """Test is_admin helper method"""
        ProjectMembership.objects.create(
            project=self.project,
            user=self.user1,
            role='admin'
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.user2,
            role='collaborator'
        )
        self.assertTrue(self.project.is_admin(self.user1))
        self.assertFalse(self.project.is_admin(self.user2))

    def test_project_is_member(self):
        """Test is_member helper method"""
        ProjectMembership.objects.create(
            project=self.project,
            user=self.user1,
            role='admin'
        )
        self.assertTrue(self.project.is_member(self.user1))
        self.assertFalse(self.project.is_member(self.user2))

    def test_get_all_members(self):
        """Test get_all_members returns correct users"""
        ProjectMembership.objects.create(project=self.project, user=self.user1, role='admin')
        ProjectMembership.objects.create(project=self.project, user=self.user2, role='collaborator')
        members = self.project.get_all_members()
        self.assertEqual(members.count(), 2)
        self.assertIn(self.user1, members)
        self.assertIn(self.user2, members)


class ProjectViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='admin_user', password='testpass123')
        self.user2 = User.objects.create_user(username='collab_user', password='testpass123')
        self.user3 = User.objects.create_user(username='other_user', password='testpass123')

    def test_project_list_requires_login(self):
        """Test that project list requires authentication"""
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_project_list_authenticated(self):
        """Test that authenticated users can access project list"""
        self.client.login(username='admin_user', password='testpass123')
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)

    def test_project_create(self):
        """Test creating a new project"""
        self.client.login(username='admin_user', password='testpass123')
        response = self.client.post(reverse('project_create'), {
            'name': 'New Project',
            'description': 'Project description'
        })
        self.assertEqual(response.status_code, 302)  # Redirects on success
        self.assertTrue(Project.objects.filter(name='New Project').exists())

        # Check creator is added as admin
        project = Project.objects.get(name='New Project')
        self.assertTrue(project.is_admin(self.user1))

    def test_project_detail_member_access(self):
        """Test that members can access project detail"""
        project = Project.objects.create(name='Test', created_by=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1, role='admin')

        self.client.login(username='admin_user', password='testpass123')
        response = self.client.get(reverse('project_detail', args=[project.id]))
        self.assertEqual(response.status_code, 200)

    def test_project_detail_non_member_denied(self):
        """Test that non-members cannot access project detail"""
        project = Project.objects.create(name='Test', created_by=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1, role='admin')

        self.client.login(username='other_user', password='testpass123')
        response = self.client.get(reverse('project_detail', args=[project.id]))
        self.assertEqual(response.status_code, 302)  # Redirects away

    def test_project_add_member_admin_only(self):
        """Test that only admins can add members"""
        project = Project.objects.create(name='Test', created_by=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1, role='admin')
        ProjectMembership.objects.create(project=project, user=self.user2, role='collaborator')

        # Admin can access add member page
        self.client.login(username='admin_user', password='testpass123')
        response = self.client.get(reverse('project_add_member', args=[project.id]))
        self.assertEqual(response.status_code, 200)

        # Collaborator cannot access add member page
        self.client.login(username='collab_user', password='testpass123')
        response = self.client.get(reverse('project_add_member', args=[project.id]))
        self.assertEqual(response.status_code, 302)  # Redirects

    def test_project_add_member_post(self):
        """Test adding a member via POST"""
        project = Project.objects.create(name='Test', created_by=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1, role='admin')

        self.client.login(username='admin_user', password='testpass123')
        response = self.client.post(reverse('project_add_member', args=[project.id]), {
            'username': 'collab_user',
            'role': 'collaborator'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProjectMembership.objects.filter(project=project, user=self.user2).exists())

    def test_project_remove_member(self):
        """Test removing a member"""
        project = Project.objects.create(name='Test', created_by=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1, role='admin')
        ProjectMembership.objects.create(project=project, user=self.user2, role='collaborator')

        self.client.login(username='admin_user', password='testpass123')
        response = self.client.post(reverse('project_remove_member', args=[project.id, self.user2.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProjectMembership.objects.filter(project=project, user=self.user2).exists())

    def test_cannot_remove_creator(self):
        """Test that the project creator cannot be removed"""
        project = Project.objects.create(name='Test', created_by=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1, role='admin')
        ProjectMembership.objects.create(project=project, user=self.user2, role='admin')

        self.client.login(username='collab_user', password='testpass123')
        response = self.client.post(reverse('project_remove_member', args=[project.id, self.user1.id]))
        # Creator should still exist
        self.assertTrue(ProjectMembership.objects.filter(project=project, user=self.user1).exists())

    def test_project_calendar_access(self):
        """Test that members can access project calendar"""
        project = Project.objects.create(name='Test', created_by=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1, role='admin')
        ProjectMembership.objects.create(project=project, user=self.user2, role='collaborator')

        # Create a task for testing
        Task.objects.create(
            title='Test Task',
            date=date.today(),
            user=self.user1,
            project=project
        )

        self.client.login(username='collab_user', password='testpass123')
        response = self.client.get(reverse('project_calendar', args=[project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')


class ProjectMembershipUniqueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.project = Project.objects.create(name='Test', created_by=self.user)

    def test_unique_membership(self):
        """Test that a user can only have one membership per project"""
        ProjectMembership.objects.create(project=self.project, user=self.user, role='admin')
        with self.assertRaises(Exception):
            ProjectMembership.objects.create(project=self.project, user=self.user, role='collaborator')


class TaskProjectIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.project = Project.objects.create(name='Test Project', created_by=self.user)

    def test_task_with_project(self):
        """Test that tasks can be linked to projects"""
        task = Task.objects.create(
            title='Project Task',
            date=date.today(),
            user=self.user,
            project=self.project
        )
        self.assertEqual(task.project, self.project)
        self.assertIn(task, self.project.tasks.all())
