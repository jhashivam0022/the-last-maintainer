package com.example.legacy.service;

import com.example.legacy.repo.UserRepository;
import org.springframework.stereotype.Service;

// Why does login look users up by email? Nobody remembers.
@Service
public class AuthService {
    private final UserRepository userRepository;

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public String login(String email, String password) {
        return userRepository.findByEmail(email) == null ? null : "token";
    }
}
