package com.example.legacy.model;

import javax.persistence.*;

@Entity
public class Order {
    @Id
    private Long id;

    @ManyToOne
    private User owner;
}
