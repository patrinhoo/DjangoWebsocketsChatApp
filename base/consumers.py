import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from django.db.models import Q
from django.contrib.auth.models import User
from .models import UserProfile, Message, Friends, FriendRequest


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope["user"]

        if (user.is_authenticated):
            self.room_group_name = "chat_%s" % user.id

            # Join room group
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name, self.channel_name
            )

            self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        try:
            if text_data_json["type"] == 'send_message':
                sender_user = User.objects.get(id=text_data_json["sender_id"])
                receiver_user = User.objects.get(
                    id=text_data_json["receiver_id"])

                sender_friends = Friends.objects.get(owner=sender_user)

                if receiver_user.userprofile in sender_friends.friends.all():
                    msg_body = text_data_json["msg_body"]
                    Message.objects.create(
                        body=msg_body, author=sender_user, receiver=receiver_user)

                    async_to_sync(self.channel_layer.group_send)(
                        "chat_%s" % text_data_json["sender_id"], {
                            "type": "message_send", "msg_body": msg_body, "receiver_id": receiver_user.id}
                    )
                    async_to_sync(self.channel_layer.group_send)(
                        "chat_%s" % text_data_json["receiver_id"], {
                            "type": "message_received", "msg_body": msg_body, "sender_id": sender_user.id}
                    )
            elif text_data_json["type"] == 'get_friend_messages':
                sender_user = User.objects.get(id=text_data_json["sender_id"])
                friend_user = User.objects.get(id=text_data_json["friend_id"])
                friend_profile = friend_user.userprofile

                messages = Message.objects.filter((Q(author=sender_user) & Q(receiver=friend_user)) | (
                    Q(author=friend_user) & Q(receiver=sender_user))).order_by('created')

                messages_list = [{'author': message.author.id,
                                  'body': message.body} for message in messages]

                async_to_sync(self.channel_layer.group_send)(
                    "chat_%s" % text_data_json["sender_id"], {
                        "type": "get_friend_messages", "messages": messages_list, "friend_name": friend_profile.name, "friend_avatar_url": friend_profile.avatar.url}
                )
            elif text_data_json["type"] == 'search_friend':
                sender_user = User.objects.get(id=text_data_json["sender_id"])
                friends = Friends.objects.get(owner=sender_user)
                friends_profiles_ids_list = [
                    friend_profile.id for friend_profile in friends.friends.all()]

                friend_requests = [
                    request.target.userprofile for request in FriendRequest.objects.filter(sender=sender_user)]

                search_result = UserProfile.objects.filter(name__contains=text_data_json["search_body"]).exclude(
                    id__in=friends_profiles_ids_list).exclude(user=sender_user)

                friends_found = [{"friend_avatar_url": profile.avatar.url, "friend_name": profile.name, "friend_id": profile.user.id}
                                 if profile not in friend_requests else {"friend_avatar_url": profile.avatar.url, "friend_name": profile.name, "friend_id": False}
                                 for profile in search_result]

                async_to_sync(self.channel_layer.group_send)(
                    "chat_%s" % text_data_json["sender_id"], {
                        "type": "search_friend", "friends_found": friends_found}
                )
            elif text_data_json["type"] == 'send_friend_request':
                sender_user = User.objects.get(id=text_data_json["sender_id"])
                friend_user = User.objects.get(id=text_data_json["friend_id"])

                my_request = FriendRequest.objects.filter(
                    Q(sender=sender_user) & Q(target=friend_user))

                if not my_request:
                    friend_request = FriendRequest.objects.filter(
                        Q(sender=friend_user) & Q(target=sender_user))
                    if friend_request:
                        my_friends = Friends.objects.get(owner=sender_user)
                        my_friends.friends.add(friend_user.userprofile)

                        friend_friends = Friends.objects.get(owner=friend_user)
                        friend_friends.friends.add(sender_user.userprofile)

                        friend_request.first().delete()

                        async_to_sync(self.channel_layer.group_send)(
                            "chat_%s" % text_data_json["sender_id"], {"type": "friend_added", "friend_id": friend_user.id,
                                                                      "friend_avatar_url": friend_user.userprofile.avatar.url, "friend_name": friend_user.userprofile.name}
                        )
                        async_to_sync(self.channel_layer.group_send)(
                            "chat_%s" % text_data_json["friend_id"], {"type": "friend_added", "friend_id": sender_user.id,
                                                                      "friend_avatar_url": sender_user.userprofile.avatar.url, "friend_name": sender_user.userprofile.name}
                        )
                    else:
                        FriendRequest.objects.create(
                            sender=sender_user, target=friend_user)

                        async_to_sync(self.channel_layer.group_send)(
                            "chat_%s" % text_data_json["sender_id"], {"type": "friend_request_send", "friend_id": friend_user.id,
                                                                      "friend_avatar_url": friend_user.userprofile.avatar.url, "friend_name": friend_user.userprofile.name}
                        )

                        async_to_sync(self.channel_layer.group_send)(
                            "chat_%s" % text_data_json["friend_id"], {"type": "friend_request_received", "friend_id": sender_user.id,
                                                                      "friend_avatar_url": sender_user.userprofile.avatar.url, "friend_name": sender_user.userprofile.name}
                        )
            elif text_data_json["type"] == 'accept_friend_request':
                sender_user = User.objects.get(id=text_data_json["sender_id"])
                friend_user = User.objects.get(id=text_data_json["friend_id"])

                friend_request = FriendRequest.objects.filter(
                    Q(sender=friend_user) & Q(target=sender_user))

                if friend_request:
                    my_friends = Friends.objects.get(owner=sender_user)
                    my_friends.friends.add(friend_user.userprofile)

                    friend_friends = Friends.objects.get(owner=friend_user)
                    friend_friends.friends.add(sender_user.userprofile)

                    friend_request.first().delete()

                    async_to_sync(self.channel_layer.group_send)(
                        "chat_%s" % text_data_json["sender_id"], {"type": "friend_added", "friend_id": friend_user.id,
                                                                  "friend_avatar_url": friend_user.userprofile.avatar.url, "friend_name": friend_user.userprofile.name}
                    )
                    async_to_sync(self.channel_layer.group_send)(
                        "chat_%s" % text_data_json["friend_id"], {"type": "friend_added", "friend_id": sender_user.id,
                                                                  "friend_avatar_url": sender_user.userprofile.avatar.url, "friend_name": sender_user.userprofile.name}
                    )
            elif text_data_json["type"] == 'reject_friend_request':
                sender_user = User.objects.get(id=text_data_json["sender_id"])
                friend_user = User.objects.get(id=text_data_json["friend_id"])

                friend_request = FriendRequest.objects.filter(
                    Q(sender=friend_user) & Q(target=sender_user))

                if friend_request:
                    friend_request.first().delete()

                    async_to_sync(self.channel_layer.group_send)(
                        "chat_%s" % text_data_json["friend_id"], {
                            "type": "friend_request_rejected", "friend_id": sender_user.id}
                    )
            elif text_data_json["type"] == 'undo_friend_request':
                sender_user = User.objects.get(id=text_data_json["sender_id"])
                friend_user = User.objects.get(id=text_data_json["friend_id"])

                friend_request = FriendRequest.objects.filter(
                    Q(sender=sender_user) & Q(target=friend_user))

                if friend_request:
                    friend_request.first().delete()

                    async_to_sync(self.channel_layer.group_send)(
                        "chat_%s" % text_data_json["friend_id"], {
                            "type": "friend_request_undone", "friend_id": sender_user.id}
                    )

        except:
            print('ERROR')

    def message_send(self, event):
        msg_body = event["msg_body"]
        receiver_id = event["receiver_id"]

        # Send message to WebSocket
        self.send(text_data=json.dumps(
            {"type": "message_send", "msg_body": msg_body, "receiver_id": receiver_id}))

    def message_received(self, event):
        msg_body = event["msg_body"]
        sender_id = event["sender_id"]

        # Send message to WebSocket
        self.send(text_data=json.dumps(
            {"type": "message_received", "msg_body": msg_body, "sender_id": sender_id}))

    def get_friend_messages(self, event):
        messages = event["messages"]
        friend_name = event["friend_name"]
        friend_avatar_url = event["friend_avatar_url"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"type": "get_friend_messages", "messages": messages,
                  "friend_name": friend_name, "friend_avatar_url": friend_avatar_url}))

    def search_friend(self, event):
        friends_found = event["friends_found"]

        # Send message to WebSocket
        self.send(text_data=json.dumps(
            {"type": "search_friend", "friends_found": friends_found}))

    def friend_added(self, event):
        friend_id = event["friend_id"]
        friend_avatar_url = event["friend_avatar_url"]
        friend_name = event["friend_name"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"type": "friend_added", "friend_id": friend_id,
                  "friend_avatar_url": friend_avatar_url, "friend_name": friend_name}))

    def friend_request_send(self, event):
        friend_id = event["friend_id"]
        friend_avatar_url = event["friend_avatar_url"]
        friend_name = event["friend_name"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"type": "friend_request_send", "friend_id": friend_id,
                  "friend_avatar_url": friend_avatar_url, "friend_name": friend_name}))

    def friend_request_received(self, event):
        friend_id = event["friend_id"]
        friend_avatar_url = event["friend_avatar_url"]
        friend_name = event["friend_name"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"type": "friend_request_received", "friend_id": friend_id,
                  "friend_avatar_url": friend_avatar_url, "friend_name": friend_name}))

    def friend_request_rejected(self, event):
        friend_id = event["friend_id"]

        # Send message to WebSocket
        self.send(text_data=json.dumps(
            {"type": "friend_request_rejected", "friend_id": friend_id}))

    def friend_request_undone(self, event):
        friend_id = event["friend_id"]

        # Send message to WebSocket
        self.send(text_data=json.dumps(
            {"type": "friend_request_undone", "friend_id": friend_id}))
