package com.example.legacy.web;

import com.example.legacy.model.User;
import com.example.legacy.repo.UserRepository;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @Autowired
    private UserRepository userRepository;

    @GetMapping("/{id}")
    public User get(@PathVariable Long id) {
        return userRepository.findById(id).orElse(null);
    }

    @RequestMapping(value = "/{id}/ping", method = RequestMethod.GET)
    public String ping(@PathVariable Long id) {
        return "pong";
    }
}
