package com.intentguard.backend.controller;

import com.intentguard.backend.dto.ChatRequest;
import com.intentguard.backend.dto.ChatResponse;
import com.intentguard.backend.model.Conversation;
import com.intentguard.backend.model.Message;
import com.intentguard.backend.service.ChatService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * ChatController
 * Manages chat interactions, user intent messages, and conversation threads.
 */
@RestController
@RequestMapping("/api")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    @PostMapping("/chat/message")
    public ResponseEntity<ChatResponse> processMessage(@Valid @RequestBody ChatRequest request) {
        ChatResponse response = chatService.processMessage(request);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/conversations/{userId}")
    public ResponseEntity<List<Conversation>> getUserConversations(@PathVariable String userId) {
        List<Conversation> conversations = chatService.getUserConversations(userId);
        return ResponseEntity.ok(conversations);
    }

    @GetMapping("/conversations/{conversationId}/messages")
    public ResponseEntity<List<Message>> getConversationMessages(@PathVariable Long conversationId) {
        List<Message> messages = chatService.getConversationMessages(conversationId);
        return ResponseEntity.ok(messages);
    }

    @DeleteMapping("/conversations/{conversationId}")
    public ResponseEntity<Map<String, Object>> deleteConversation(@PathVariable Long conversationId,
                                                                 @RequestParam(defaultValue = "USER_1") String userId) {
        chatService.deleteConversation(conversationId, userId);
        Map<String, Object> body = new HashMap<>();
        body.put("success", true);
        body.put("message", "Conversation deleted successfully");
        return ResponseEntity.ok(body);
    }
}
