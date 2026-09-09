package com.intentguard.backend.service;

import com.intentguard.backend.dto.ChatRequest;
import com.intentguard.backend.dto.ChatResponse;
import com.intentguard.backend.exception.ResourceNotFoundException;
import com.intentguard.backend.model.Conversation;
import com.intentguard.backend.model.Intent;
import com.intentguard.backend.model.Message;
import com.intentguard.backend.repository.ConversationRepository;
import com.intentguard.backend.repository.MessageRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * ChatService
 * Manages continuous conversation threads, message logs, and intent orchestration.
 */
@Service
public class ChatService {

    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    private final IntentService intentService;

    public ChatService(ConversationRepository conversationRepository,
                       MessageRepository messageRepository,
                       IntentService intentService) {
        this.conversationRepository = conversationRepository;
        this.messageRepository = messageRepository;
        this.intentService = intentService;
    }

    @Transactional
    public ChatResponse processMessage(ChatRequest request) {
        String userId = request.getUserId() != null ? request.getUserId() : "USER_1";
        Long conversationId = request.getConversationId();

        // 1. Create new conversation if conversationId is null
        if (conversationId == null) {
            String title = generateTitle(request.getMessage());
            Conversation conversation = new Conversation();
            conversation.setUserId(userId);
            conversation.setTitle(title);
            conversationId = conversationRepository.save(conversation);
        } else {
            // Verify conversation exists
            final Long existingId = conversationId;
            conversationRepository.findById(existingId)
                    .orElseThrow(() -> new ResourceNotFoundException("Conversation not found with id: " + existingId));
        }

        final Long activeConversationId = conversationId;

        // 2. Save User Message
        Message userMsg = new Message();
        userMsg.setConversationId(activeConversationId);
        userMsg.setSender("USER");
        userMsg.setContent(request.getMessage());
        messageRepository.save(userMsg);

        // 3. Extract Intent
        Intent intent = intentService.extractIntent(request.getMessage());

        // 4. Save Agent Acknowledgment Message
        String agentReplyText = "I'll search across available marketplaces and compare the best matches based on your requirements.";
        Message agentMsg = new Message();
        agentMsg.setConversationId(activeConversationId);
        agentMsg.setSender("AGENT");
        agentMsg.setContent(agentReplyText);
        messageRepository.save(agentMsg);

        return new ChatResponse(activeConversationId, request.getMessage(), agentReplyText, intent);
    }

    public List<Conversation> getUserConversations(String userId) {
        return conversationRepository.findByUserId(userId);
    }

    public List<Message> getConversationMessages(Long conversationId) {
        return messageRepository.findByConversationId(conversationId);
    }

    public void deleteConversation(Long conversationId, String userId) {
        int rows = conversationRepository.deleteByIdAndUserId(conversationId, userId);
        if (rows == 0) {
            throw new ResourceNotFoundException("Conversation not found or unauthorized");
        }
    }

    private String generateTitle(String userText) {
        if (userText == null || userText.trim().isEmpty()) return "New Intent";
        String clean = userText.trim();
        if (clean.length() > 30) {
            return clean.substring(0, 27) + "...";
        }
        return clean;
    }
}
