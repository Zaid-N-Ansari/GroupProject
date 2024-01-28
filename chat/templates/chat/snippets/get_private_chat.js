function getPrivateChat(id){
	payload = {
		"csrfmiddlewaretoken": "{{ csrf_token }}",
		"user2_id": id,
	};
	$.ajax({
		type: "POST",
		dataType: "json",
		url: "{% url 'chat:create-private-chat' %}",
		data: payload,
		timeout: 5000,
		success: function(data) {
			console.log("SUCCESS", data);
			if(data['response'] == "Chat Retrieved"){
				chatroomId = data['chatroom_id'];
				OnGetOrCreateChatroomSuccess(chatroomId);
			}
			else if(data['response'] != null){
				alert(data['response']);
			}
		},
		error: function(data) {
			console.error("ERROR...", data);
			alert("Something went wrong.");
		},
	});
}


function OnGetOrCreateChatroomSuccess(chatroomId){
	const url = "{% url 'chat:private-chat-room' %}?room_id=" + chatroomId;
	window.location.replace(url).focus();
}
