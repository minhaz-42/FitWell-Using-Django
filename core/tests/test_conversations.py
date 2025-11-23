from django.test import TestCase, Client
from django.contrib.auth.models import User
import json


class ConversationAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test_conv_user')
        self.client.force_login(self.user)

    def test_chat_creates_conversation_and_messages(self):
        resp = self.client.post('/api/v1/chat', json.dumps({'message': 'Hello test chat'}), content_type='application/json', **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('conversation_id', data)
        self.assertIn('user_message_id', data)
        self.assertIn('ai_message_id', data)

    def test_conversation_list_has_unread_count(self):
        # create a chat
        resp = self.client.post('/api/v1/chat', json.dumps({'message': 'Hello unread check'}), content_type='application/json', **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(resp.status_code, 200)

        # list conversations
        resp = self.client.get('/api/conversations/?limit=10&offset=0', **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('conversations', data)
        convs = data['conversations']
        self.assertTrue(len(convs) >= 1)
        # unread_count should be present
        self.assertIn('unread_count', convs[0])