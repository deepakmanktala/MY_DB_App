package com.deepakmanktala.EcommerceApp;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

@RestController
public class UserController {

    List <User> userList = new ArrayList<User>();

    @GetMapping("/api/users")
    public List <User> getallusers(){

        return userList;

    }
}
