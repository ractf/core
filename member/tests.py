from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST, \
    HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase


class MemberTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='test-self', email='test-self@example.org')
        user.save()
        self.user = user

    def test_str(self):
        user = get_user_model()(username='test-str', email='test-str@example.org')
        self.assertEquals(str(user), user.username)

    def test_self_status(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('member-self'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_self_status_unauth(self):
        response = self.client.get(reverse('member-self'))
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_self_change_email(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse('member-self'), data={'email': 'test-self2@example.org'})
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_self_change_email_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse('member-self'), data={'email': 'test-self'})
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    def test_self_change_email_token_change(self):
        pr_token = self.user.password_reset_token
        ev_token = self.user.email_token
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse('member-self'), data={'email': 'test-self3@example.org'})
        user = get_user_model().objects.get(id=self.user.id)
        self.assertNotEquals(pr_token, user.password_reset_token)
        self.assertNotEquals(ev_token, user.email_token)

    def test_self_get_email(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('member-self'))
        self.assertEquals(response.data['email'], 'test-self@example.org')

    def test_self_update_email(self):
        self.client.force_authenticate(self.user)
        self.client.get(reverse('member-self'))
        self.client.put(reverse('member-self'), data={'email': 'test-self3@example.org'})
        response = self.client.get(reverse('member-self'))
        self.assertEquals(response.data['email'], 'test-self3@example.org')


class MemberViewSetTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='test-member', email='test-member@example.org')
        user.save()
        self.user = user
        user = get_user_model()(username='test-admin', email='test-admin@example.org')
        user.is_staff = True
        user.save()
        self.admin_user = user

    def test_visible_admin(self):
        user = get_user_model()(username='test-member-invisible', email='test-member-invisible@example.org')
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse('member-list'))
        self.assertEquals(len(response.data['results']), 3)

    def test_visible_not_admin(self):
        user = get_user_model()(username='test-member-invisible', email='test-member-invisible@example.org')
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('member-list'))
        self.assertEquals(len(response.data['results']), 0)

    def test_visible_detail_admin(self):
        user = get_user_model()(username='test-member-invisible', email='test-member-invisible@example.org')
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse('member-detail', kwargs={'pk': user.id}))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_visible_detail_not_admin(self):
        user = get_user_model()(username='test-member-invisible', email='test-member-invisible@example.org')
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('member-detail', kwargs={'pk': user.id}))
        self.assertEquals(response.status_code, HTTP_404_NOT_FOUND)

    def test_view_email_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse('member-detail', kwargs={'pk': self.user.id}))
        self.assertTrue('email' in response.data)

    def test_view_email_not_admin(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('member-detail', kwargs={'pk': self.admin_user.id}))
        self.assertFalse('email' in response.data)

    def test_view_member(self):
        self.admin_user.is_visible = True
        self.admin_user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('member-detail', kwargs={'pk': self.admin_user.id}))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_patch_member(self):
        self.admin_user.is_visible = True
        self.admin_user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(reverse('member-detail', kwargs={'pk': self.admin_user.id}),
                                     data={'username': 'test'})
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_patch_member_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.patch(reverse('member-detail', kwargs={'pk': self.user.id}),
                                     data={'username': 'test'})
        self.assertEquals(response.status_code, HTTP_200_OK)
