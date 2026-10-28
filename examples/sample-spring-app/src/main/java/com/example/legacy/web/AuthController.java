package com.example.legacy.web;

import com.example.legacy.service.AuthService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public String login(@RequestBody String body) {
        return authService.login(body, "");
    }

    @PostMapping(value = "/register")
    public String register(@RequestBody String body) {
        return "ok";
    }
}
