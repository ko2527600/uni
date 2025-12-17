"""
Real-time chat event handlers using Flask-SocketIO
"""

from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio, db
from app.models import ForumPost, ForumReply, User
from datetime import datetime

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        print(f'User {current_user.username} connected')
    else:
        print('Anonymous user connected')

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        print(f'User {current_user.username} disconnected')

@socketio.on('join')
def on_join(data):
    """Handle user joining a chat room (class group)"""
    if not current_user.is_authenticated:
        return
    
    room = data.get('room')
    if not room:
        return
    
    # Verify user belongs to this class group
    try:
        room_id = int(room)
        if current_user.class_group_id != room_id:
            emit('error', {'message': 'Access denied to this chat room'})
            return
    except (ValueError, TypeError):
        emit('error', {'message': 'Invalid room ID'})
        return
    
    join_room(room)
    emit('status', {
        'message': f'{current_user.username} joined the chat',
        'user': current_user.username,
        'timestamp': datetime.now().strftime('%H:%M')
    }, to=room)
    
    print(f'User {current_user.username} joined room {room}')

@socketio.on('leave')
def on_leave(data):
    """Handle user leaving a chat room"""
    if not current_user.is_authenticated:
        return
    
    room = data.get('room')
    if not room:
        return
    
    leave_room(room)
    emit('status', {
        'message': f'{current_user.username} left the chat',
        'user': current_user.username,
        'timestamp': datetime.now().strftime('%H:%M')
    }, to=room)
    
    print(f'User {current_user.username} left room {room}')

@socketio.on('message')
def handle_message(data):
    """Handle real-time chat messages"""
    print(f'📨 Received message event from {current_user.username if current_user.is_authenticated else "anonymous"}: {data}')
    
    if not current_user.is_authenticated:
        print('❌ User not authenticated')
        emit('error', {'message': 'Authentication required'})
        return
    
    message_text = data.get('msg', '').strip()
    room = data.get('room')
    
    print(f'📝 Message: "{message_text}", Room: {room}')
    
    if not message_text or not room:
        print('❌ Missing message or room')
        emit('error', {'message': 'Message and room are required'})
        return
    
    # Verify user belongs to this class group
    try:
        room_id = int(room)
        if current_user.class_group_id != room_id:
            emit('error', {'message': 'Access denied to this chat room'})
            return
    except (ValueError, TypeError):
        emit('error', {'message': 'Invalid room ID'})
        return
    
    try:
        # Save message to database as a ForumReply (for persistence)
        # First, get or create a general chat post for this class
        chat_post = ForumPost.query.filter_by(
            class_group_id=room,
            title='Class Chat'
        ).first()
        
        if not chat_post:
            # Create a general chat post for this class
            chat_post = ForumPost(
                title='Class Chat',
                content='Real-time class discussion',
                user_id=current_user.id,
                class_group_id=room
            )
            db.session.add(chat_post)
            db.session.commit()
        
        # Create the chat message as a reply
        chat_message = ForumReply(
            content=message_text,
            user_id=current_user.id,
            post_id=chat_post.id
        )
        db.session.add(chat_message)
        db.session.commit()
        
        # Prepare message data for broadcast
        message_data = {
            'id': chat_message.id,
            'msg': message_text,
            'user': current_user.username,
            'user_initials': current_user.avatar_initials,
            'user_id': current_user.id,
            'timestamp': chat_message.timestamp.strftime('%H:%M'),
            'full_timestamp': chat_message.timestamp.strftime('%B %d, %Y at %H:%M'),
            'room': room
        }
        
        # Broadcast message to all users in the room
        emit('message', message_data, to=room)
        
        print(f'Message from {current_user.username} in room {room}: {message_text}')
        
    except Exception as e:
        print(f'Error saving message: {e}')
        emit('error', {'message': 'Failed to send message'})
        db.session.rollback()

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicators"""
    if not current_user.is_authenticated:
        return
    
    room = data.get('room')
    is_typing = data.get('typing', False)
    
    if not room:
        return
    
    # Verify user belongs to this class group
    try:
        room_id = int(room)
        if current_user.class_group_id != room_id:
            return
    except (ValueError, TypeError):
        return
    
    # Broadcast typing status to other users in the room
    emit('typing', {
        'user': current_user.username,
        'user_id': current_user.id,
        'typing': is_typing
    }, to=room, include_self=False)

@socketio.on('get_chat_history')
def handle_get_chat_history(data):
    """Send recent chat history to newly connected user"""
    if not current_user.is_authenticated:
        return
    
    room = data.get('room')
    if not room:
        return
    
    try:
        room_id = int(room)
        if current_user.class_group_id != room_id:
            return
    except (ValueError, TypeError):
        return
    
    try:
        # Get the class chat post
        chat_post = ForumPost.query.filter_by(
            class_group_id=room,
            title='Class Chat'
        ).first()
        
        if not chat_post:
            emit('chat_history', {'messages': []})
            return
        
        # Get recent messages (last 50)
        recent_messages = ForumReply.query.filter_by(
            post_id=chat_post.id
        ).order_by(ForumReply.timestamp.desc()).limit(50).all()
        
        # Reverse to show oldest first
        recent_messages.reverse()
        
        # Format messages
        messages = []
        for msg in recent_messages:
            messages.append({
                'id': msg.id,
                'msg': msg.content,
                'user': msg.author.username,
                'user_initials': msg.author.avatar_initials,
                'user_id': msg.user_id,
                'timestamp': msg.timestamp.strftime('%H:%M'),
                'full_timestamp': msg.timestamp.strftime('%B %d, %Y at %H:%M')
            })
        
        emit('chat_history', {'messages': messages})
        
    except Exception as e:
        print(f'Error getting chat history: {e}')
        emit('chat_history', {'messages': []})