// Websocket Connection
const userID = JSON.parse(document.getElementById('user_id').textContent);

// HOME PAGE - OPTIONS
const showConversationsButton = document.getElementsByClassName('show-conversations')[0]
const showAddFriendButton = document.getElementsByClassName('show-add-friend')[0]
const showFriendRequestsButton = document.getElementsByClassName('show-friend-requests')[0]
const showMyProfileButton = document.getElementsByClassName('show-my-profile')[0]

const conversations = document.getElementsByClassName('conversations')[0]
const addFriend = document.getElementsByClassName('add-friend')[0]
const friendRequests = document.getElementsByClassName('friend-requests')[0]
const myProfile = document.getElementsByClassName('my-profile')[0]

let activeConversationID;

// SCROLL CONTENT DOWN
const scrollToBottom = (id) => {
    const element = document.getElementById(id);
    element.scrollTop = element.scrollHeight;
}

const chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/'
    + userID
    + '/'
);

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    // console.log(data);

    if (data.type === "get_friend_messages"){   
        const messagesWrapper = document.getElementById('messages-wrapper');
        messagesWrapper.innerHTML = '';

        document.getElementById('actual-conversation').innerHTML = data.friend_name;
        document.getElementById('actual-conversation-img').src = data.friend_avatar_url;

        for (let i = 0; i < data.messages.length; i++) {
            if (data.messages[i].author === userID) {
                messagesWrapper.insertAdjacentHTML(
                    'beforeend',
                    `<div class="my-msg p-3 my-3 ms-auto me-lg-5 me-3 border">
                    ${data.messages[i].body}
                    </div>`,
                );
            } else {
                messagesWrapper.insertAdjacentHTML(
                    'beforeend',
                    `<div class="friend-msg p-3 my-3 ms-lg-5 ms-3 me-auto border">
                    ${data.messages[i].body}
                    </div>`,
                );
            }
        }

        scrollToBottom('messages-wrapper');
    } else if (data.type === "message_send"){
        const messagesWrapper = document.getElementById('messages-wrapper');

        messagesWrapper.insertAdjacentHTML(
            'beforeend',
            `<div class="my-msg p-3 my-3 ms-auto me-lg-5 me-3 border">
            ${data.msg_body}
            </div>`,
        );

        scrollToBottom('messages-wrapper');
    } else if (data.type === "message_received"){
        if (data.sender_id == activeConversationID){
            const messagesWrapper = document.getElementById('messages-wrapper');

            messagesWrapper.insertAdjacentHTML(
                'beforeend',
                `<div class="friend-msg p-3 my-3 ms-lg-5 ms-3 me-auto border">
                ${data.msg_body}
                </div>`,
            );

            scrollToBottom('messages-wrapper');
        } else {
            const friends_list = document.getElementsByClassName('friend-on-list')
            for (i=0; i<friends_list.length; i++){
                if (data.sender_id == friends_list[i].id){
                    new_msg = friends_list[i].getElementsByClassName('new-msg')[0]
                    new_msg.style.display = "block";
                    break;
                }

            }
        }
    } else if (data.type === "search_friend"){
        const friendsFoundWrapper = document.getElementById('friends-found-wrapper');

        for (let i = 0; i < data.friends_found.length; i++) {

            if (data.friends_found[i].friend_id){
                friendsFoundWrapper.insertAdjacentHTML(
                    'beforeend',
                    `<div class="friend-on-list row w-100 m-0 border">
                        <div class="h-100 col-3">
                            <img src="${data.friends_found[i].friend_avatar_url}" alt="" class="friend-img rounded-circle h-75">
                        </div>
                        <div class="col-5">
                            <div class="d-flex align-items-center h-100 fw-bold">
                                ${data.friends_found[i].friend_name}
                            </div>
                        </div>
                        <div class="col-4 fs-6">
                            <button id="${data.friends_found[i].friend_id}" type="button" class="add-friend-btn btn mt-3 float-end">Dodaj</button>
                        </div>
                    </div>`
                )
            } else {
                friendsFoundWrapper.insertAdjacentHTML(
                    'beforeend',
                    `<div class="friend-on-list row w-100 m-0 border">
                        <div class="h-100 col-3">
                            <img src="${data.friends_found[i].friend_avatar_url}" alt="" class="friend-img rounded-circle h-75">
                        </div>
                        <div class="col-5">
                            <div class="d-flex align-items-center h-100 fw-bold">
                                ${data.friends_found[i].friend_name}
                            </div>
                        </div>
                        <div class="col-4 fs-6">
                            <button type="button" class="btn btn-warning text-white mt-3 float-end">Wysłano</button>
                        </div>
                    </div>`
                )
            }
        }

        document.querySelectorAll('.add-friend-btn').forEach(item => {
            item.addEventListener('click', () => {

                item.parentElement.parentElement.remove()

                chatSocket.send(JSON.stringify({
                    'type': 'send_friend_request',
                    'sender_id': userID,
                    'friend_id': Number(item.id)
                }));
            })
        })
    } else if (data.type === "friend_added"){
        conversations.insertAdjacentHTML(
            'beforeend',
            `<div id="${data.friend_id}" class="friend-on-list row w-100 m-0 border">
                <div class="h-100 col-3">
                    <img src="${data.friend_avatar_url}" alt="" class="friend-img rounded-circle h-75">
                </div>
                <div class="col-5">
                    <div class="d-flex align-items-center h-100 fw-bold">
                        ${data.friend_name}
                    </div>
                </div>
                <div class="col-4 fs-6 d-flex align-items-center justify-content-center">
                    <div class="new-msg">
                        !
                    </div>
                </div>
            </div>`
        );

        const friend_added = document.querySelector('.friend-on-list:last-of-type')

        friend_added.addEventListener('click', () => {
            activeConversationID = friend_added.id;
    
            const new_msg = friend_added.getElementsByClassName('new-msg')[0]
            new_msg.style.display = "none";
    
            chatSocket.send(JSON.stringify({
                'type': 'get_friend_messages',
                'sender_id': userID,
                'friend_id': Number(activeConversationID)
            }));
        })

        const received_requests = document.getElementsByClassName('received-requests')[0]
        const received_request_accept = received_requests.getElementsByClassName('accept-btn')
        for (i=0; i<received_request_accept.length; i++){
            if (received_request_accept[i].id === friend_added.id){
                received_request_accept[i].parentElement.parentElement.remove();
                break;
            }
        }

        const send_requests = document.getElementsByClassName('send-requests')[0]
        const send_request_undo = send_requests.getElementsByClassName('undo-btn')
        for (i=0; i<send_request_undo.length; i++){
            if (send_request_undo[i].id === friend_added.id){
                send_request_undo[i].parentElement.parentElement.remove();
                break;
            }
        }
    } else if (data.type === "friend_request_send"){
        const send_requests = document.getElementsByClassName('send-requests')[0]

        send_requests.insertAdjacentHTML(
            'beforeend',
            `<div class="friend-request-list row w-100 m-0 border">
                <div class="h-100 col-3">
                    <img src="${data.friend_avatar_url}" alt="" class="friend-img rounded-circle h-75">
                </div>
                <div class="col-5">
                    <div class="d-flex align-items-center h-100 fw-bold">
                        ${data.friend_name}
                    </div>
                </div>
                <div class="col-4 fs-6 d-flex align-items-center justify-content-center">
                    <div id="${data.friend_id}"  class="btn btn-danger undo-btn">
                        COFNIJ
                    </div>
                </div>
            </div>`
        )    
        
        const send_request_undo = send_requests.getElementsByClassName('undo-btn')
        for (i=0; i<send_request_undo.length; i++){
            if (send_request_undo[i].id == data.friend_id){
                send_request_undo[i].addEventListener('click', () => {
                    chatSocket.send(JSON.stringify({
                        'type': 'undo_friend_request',
                        'sender_id': userID,
                        'friend_id': Number(send_request_undo[i].id)
                    }));
    
                    send_request_undo[i].parentElement.parentElement.remove();
                });
                break;
            }
        }
    } else if (data.type === "friend_request_received") {
        const received_requests = document.getElementsByClassName('received-requests')[0]

        received_requests.insertAdjacentHTML(
            'beforeend',
            `<div class="friend-request-list row w-100 m-0 border">
                <div class="h-100 col-3">
                    <img src="${data.friend_avatar_url}" alt="" class="friend-img rounded-circle h-75">
                </div>
                <div class="col-5">
                    <div class="d-flex align-items-center h-100 fw-bold">
                        ${data.friend_name}
                    </div>
                </div>
                <div class="col-4 fs-6 d-flex align-items-center justify-content-center">
                    <div id="${data.friend_id}" class="btn m-md-2 m-0 accept-btn">
                        &#10003;
                    </div>
                    <div id="${data.friend_id}" class="btn btn-danger reject-btn">
                        &#10005;
                    </div>
                </div>
            </div>`
        )    
        
        const accept_request_btn = received_requests.querySelectorAll('.accept-btn')
        const reject_request_btn = received_requests.querySelectorAll('.reject-btn')
        for (i=0; i<accept_request_btn.length; i++){
            if (accept_request_btn[i].id == data.friend_id){
                accept_request_btn[i].addEventListener('click', () => {
                    chatSocket.send(JSON.stringify({
                        'type': 'accept_friend_request',
                        'sender_id': userID,
                        'friend_id': Number(accept_request_btn[i].id)
                    }));
    
                    accept_request_btn[i].parentElement.parentElement.remove();
                });
                break;
            }
        }
        for (i=0; i<reject_request_btn.length; i++){
            if (reject_request_btn[i].id == data.friend_id){
                reject_request_btn[i].addEventListener('click', () => {
                    chatSocket.send(JSON.stringify({
                        'type': 'reject_friend_request',
                        'sender_id': userID,
                        'friend_id': Number(reject_request_btn[i].id)
                    }));
            
                    reject_request_btn[i].parentElement.parentElement.remove();
                });
                break;
            }
        }

    } else if (data.type === "friend_request_rejected") {
        const send_requests = document.querySelectorAll('.undo-btn')
        for (i=0; i<send_requests.length; i++){
            if (send_requests[i].id == data.friend_id){
                send_requests[i].parentElement.parentElement.remove();
                break;
            }
        }
    } else if (data.type === "friend_request_undone") {
        const received_requests = document.querySelectorAll('.accept-btn')
        for (i=0; i<received_requests.length; i++){
            if (received_requests[i].id == data.friend_id){
                received_requests[i].parentElement.parentElement.remove();
                break;
            }
        }
    }
};

// HANDLE CONVERSATIONS
document.querySelectorAll('.friend-on-list').forEach(item => {
    item.addEventListener('click', () => {
        activeConversationID = item.id;

        new_msg = item.getElementsByClassName('new-msg')[0]
        new_msg.style.display = "none";

        chatSocket.send(JSON.stringify({
            'type': 'get_friend_messages',
            'sender_id': userID,
            'friend_id': Number(activeConversationID)
        }));
    })
})

showConversationsButton.addEventListener('click', () => {
    conversations.style.display = "block";
    addFriend.style.display = "none";
    friendRequests.style.display = "none";
    myProfile.style.display = "none";
})

// HANDLE ADD FRIENDS
showAddFriendButton.addEventListener('click', () => {
    conversations.style.display = "none";
    addFriend.style.display = "block";
    friendRequests.style.display = "none";
    myProfile.style.display = "none";
})

const searchFriendBtn = document.getElementById('search-friend-btn');
const serachFriendInput = document.getElementById('search-friend-input');

searchFriendBtn.addEventListener('click', () => {
    const friendsFoundWrapper = document.getElementById('friends-found-wrapper');
    friendsFoundWrapper.innerHTML = '';

    if (serachFriendInput.value) {
        chatSocket.send(JSON.stringify({
            'type': 'search_friend',
            'sender_id': userID,
            'search_body': serachFriendInput.value
        }));
    }
});

// HANDLE FRIEND REQUESTS
showFriendRequestsButton.addEventListener('click', () => {
    conversations.style.display = "none";
    addFriend.style.display = "none";
    friendRequests.style.display = "block";
    myProfile.style.display = "none";
})

// ACCEPT FRIEND REQUEST
document.querySelectorAll('.accept-btn').forEach(item => {
    item.addEventListener('click', () => {
        chatSocket.send(JSON.stringify({
            'type': 'accept_friend_request',
            'sender_id': userID,
            'friend_id': Number(item.id)
        }));

        item.parentElement.parentElement.remove();
    })
})

// REJECT FRIEND REQUEST
document.querySelectorAll('.reject-btn').forEach(item => {
    item.addEventListener('click', () => {
        chatSocket.send(JSON.stringify({
            'type': 'reject_friend_request',
            'sender_id': userID,
            'friend_id': Number(item.id)
        }));
        
        item.parentElement.parentElement.remove();
    })
})

// UNDO FRIEND REQUEST
document.querySelectorAll('.undo-btn').forEach(item => {
    item.addEventListener('click', () => {
        chatSocket.send(JSON.stringify({
            'type': 'undo_friend_request',
            'sender_id': userID,
            'friend_id': Number(item.id)
        }));
        
        item.parentElement.parentElement.remove();
    })
})


// HANDLE PROFILE UPDATE
showMyProfileButton.addEventListener('click', () => {
    conversations.style.display = "none";
    addFriend.style.display = "none";
    friendRequests.style.display = "none";
    myProfile.style.display = "block";
})

const updateProfileBtn = document.getElementById('update-profile-btn');
const usernameInput = document.getElementById('username-input');

updateProfileBtn.addEventListener('click', () => {
    
    // TODO: websocketUpdateProfile
    console.log(usernameInput.value);

});

// HANDLE SENDING MESSAGES 
const sendMessageButton = document.getElementsByClassName('send-msg')[0]
const msgInput = document.getElementsByClassName('msg-input')[0]

sendMessageButton.addEventListener('click', () => {

    if (msgInput.value){

        chatSocket.send(JSON.stringify({
            'type': 'send_message',
            'sender_id': userID,
            'receiver_id': Number(activeConversationID),
            'msg_body': msgInput.value
        }));

        msgInput.value = '';

    }
})

