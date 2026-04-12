package com.deepakmanktala.EcommerceApp;

import org.springframework.web.bind.annotation.*;

@RestController
public class HelloController {
    @GetMapping("/hello")
    public String sayHello() {
        return "Hello World!";
    }

    @PostMapping("/hellopost")
    public String helloPost(@RequestBody String name) {
        return "Hello " + name + "!";
    }



    // Controller talks to the users/brwosers --> routes to Srevice layer, Srevice layer has the business logi and rules, talks to repository and repository talks to the databases
}
