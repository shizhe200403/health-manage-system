import json

from django.http import StreamingHttpResponse
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .context import build_user_context
from .llm import stream_chat
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def conversations(request):
    if request.method == "POST":
        conv = Conversation.objects.create(user=request.user)
        return Response({"code": 0, "message": "success", "data": ConversationSerializer(conv).data}, status=status.HTTP_201_CREATED)
    qs = Conversation.objects.filter(user=request.user)[:20]
    return Response({"code": 0, "message": "success", "data": ConversationSerializer(qs, many=True).data})


@api_view(["GET", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def conversation_detail(request, pk):
    try:
        conv = Conversation.objects.get(pk=pk, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"code": 1, "message": "not found"}, status=404)
    if request.method == "DELETE":
        conv.delete()
        return Response({"code": 0, "message": "success"})
    msgs = conv.messages.all()
    return Response({"code": 0, "message": "success", "data": {
        "conversation": ConversationSerializer(conv).data,
        "messages": MessageSerializer(msgs, many=True).data,
    }})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def chat(request, pk):
    try:
        conv = Conversation.objects.get(pk=pk, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"code": 1, "message": "not found"}, status=404)

    user_message = (request.data.get("message") or "").strip()
    if not user_message:
        return Response({"code": 1, "message": "message is required"}, status=400)

    # Save user message
    Message.objects.create(conversation=conv, role="user", content=user_message)

    # Auto-title from first message
    if conv.title == "新对话":
        conv.title = user_message[:50]
        conv.save(update_fields=["title", "updated_at"])

    # Build context and history
    system_prompt = build_user_context(request.user)
    history = list(conv.messages.order_by("created_at").values_list("role", "content"))
    messages = [{"role": r, "content": c} for r, c in history[-20:]]

    def event_stream():
        full_response = ""
        for chunk in stream_chat(system_prompt, messages):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        Message.objects.create(conversation=conv, role="assistant", content=full_response)
        conv.save(update_fields=["updated_at"])
        yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
