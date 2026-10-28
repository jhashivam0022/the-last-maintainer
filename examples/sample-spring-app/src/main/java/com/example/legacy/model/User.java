package com.example.legacy.model;

import javax.persistence.*;
import java.util.List;

@Entity
@Table(name = "app_users")
public class User {
    @Id
    private Long id;
    private String email;

    @OneToMany
    private List<Order> orders;
}
